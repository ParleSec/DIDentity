"""
DIDentity Load Testing Module

This module provides comprehensive load testing capabilities for the DIDentity platform.
It tests all major services including authentication, DID management, credential issuance,
and verification under various load conditions.

Key Features:
- Asynchronous load testing with configurable concurrency
- Full workflow testing (register → DID → credential → verify)
- Individual service endpoint testing
- Real-time metrics collection and reporting
- Support for different load patterns (burst, sustained, ramp-up)
- Detailed performance analysis with percentile calculations

Usage:
    tester = DIDentityLoadTester()
    await tester.run_mixed_load_test(duration=60, concurrent_users=10)
"""

import asyncio
import aiohttp
import time
import json
import random
import statistics
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import psutil
import os
import argparse
import sys
from types import SimpleNamespace

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LoadTestMetrics:
    """Metrics collected during load testing"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_duration: float = 0.0
    average_response_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    p50_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    requests_per_second: float = 0.0
    errors_by_type: Dict[str, int] = None
    response_times: List[float] = None
    
    def __post_init__(self):
        if self.errors_by_type is None:
            self.errors_by_type = {}
        if self.response_times is None:
            self.response_times = []
    
    def add_response_time(self, time: float):
        """Add a response time measurement"""
        self.response_times.append(time)
        self.min_response_time = min(self.min_response_time, time)
        self.max_response_time = max(self.max_response_time, time)
    
    def add_error(self, error_type: str):
        """Add an error count"""
        self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1
    
    def calculate_percentiles(self):
        """Calculate response time percentiles"""
        if self.response_times:
            sorted_times = sorted(self.response_times)
            self.average_response_time = statistics.mean(sorted_times)
            self.p50_response_time = statistics.median(sorted_times)
            if len(sorted_times) >= 20:  # Only calculate if we have enough data
                self.p95_response_time = sorted_times[int(0.95 * len(sorted_times))]
                self.p99_response_time = sorted_times[int(0.99 * len(sorted_times))]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for JSON serialization"""
        return {
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate': (self.successful_requests / max(self.total_requests, 1)) * 100,
            'total_duration': round(self.total_duration, 2),
            'average_response_time': round(self.average_response_time, 3),
            'min_response_time': round(self.min_response_time, 3) if self.min_response_time != float('inf') else 0,
            'max_response_time': round(self.max_response_time, 3),
            'p50_response_time': round(self.p50_response_time, 3),
            'p95_response_time': round(self.p95_response_time, 3),
            'p99_response_time': round(self.p99_response_time, 3),
            'requests_per_second': round(self.requests_per_second, 2),
            'errors_by_type': self.errors_by_type
        }


class DIDentityLoadTester:
    """Load tester for DIDentity services"""
    
    def __init__(self):
        self.services = {
            'auth': 'http://localhost:8004',
            'did': 'http://localhost:8001',
            'credential': 'http://localhost:8002',
            'verification': 'http://localhost:8003'
        }
        self.session = None
        self.active_users = []
        self.response_times = []
        self.errors = {}
        self.requests_sent = 0
        self.successful_requests = 0
        self.failed_requests = 0
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def register_user(self, user_id: str) -> Tuple[bool, float, Optional[str]]:
        """Register a new user using the correct /signup endpoint"""
        start_time = time.time()
        
        try:
            payload = {
                'username': f'loadtest_user_{user_id}_{int(time.time())}',
                'email': f'loadtest_{user_id}_{int(time.time())}@example.com',
                'password': f'testpass_{random.randint(1000, 9999)}'
            }
            
            async with self.session.post(
                f"{self.services['auth']}/signup",
                json=payload,
                timeout=30
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    token = data.get('access_token')
                    return True, response_time, token
                else:
                    return False, response_time, f"HTTP {response.status}"
                    
        except Exception as e:
            response_time = time.time() - start_time
            return False, response_time, str(e)
    
    async def create_did(self, token: str, user_id: str) -> Tuple[bool, float, Optional[str]]:
        """Create a DID for authenticated user"""
        start_time = time.time()
        
        try:
            # Generate a Base58 identifier for key method
            base58_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
            identifier = ''.join(random.choice(base58_chars) for _ in range(16))
            
            payload = {
                'method': 'key',
                'identifier': identifier
            }
            
            headers = {'Authorization': f'Bearer {token}'}
            
            async with self.session.post(
                f"{self.services['did']}/dids",
                json=payload,
                headers=headers,
                timeout=30
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    did = data.get('id')
                    return True, response_time, did
                else:
                    return False, response_time, f"HTTP {response.status}"
                    
        except Exception as e:
            response_time = time.time() - start_time
            return False, response_time, str(e)
    
    async def issue_credential(self, did: str) -> Tuple[bool, float, Optional[str]]:
        """Issue a credential for a DID"""
        start_time = time.time()
        
        try:
            payload = {
                'holder_did': did,
                'credential_data': {
                    'name': f'Load Test User {random.randint(1000, 9999)}',
                    'degree': 'Bachelor of Computer Science',
                    'institution': 'DIDentity University',
                    'graduation_year': random.randint(2020, 2024)
                }
            }
            
            async with self.session.post(
                f"{self.services['credential']}/credentials/issue",
                json=payload,
                timeout=30
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    cred_id = data.get('credential_id')
                    return True, response_time, cred_id
                else:
                    return False, response_time, f"HTTP {response.status}"
                    
        except Exception as e:
            response_time = time.time() - start_time
            return False, response_time, str(e)
    
    async def verify_credential(self, credential_id: str) -> Tuple[bool, float, Optional[str]]:
        """Verify a credential"""
        start_time = time.time()
        
        try:
            payload = {'credential_id': credential_id}
            
            async with self.session.post(
                f"{self.services['verification']}/credentials/verify",
                json=payload,
                timeout=30
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    status = data.get('status', 'unknown')
                    return True, response_time, status
                else:
                    return False, response_time, f"HTTP {response.status}"
                    
        except Exception as e:
            response_time = time.time() - start_time
            return False, response_time, str(e)
    
    async def run_complete_workflow(self, user_id: str) -> Dict[str, Any]:
        """Run complete DIDentity workflow for a single user"""
        workflow_start = time.time()
        results = {
            'user_id': user_id,
            'steps': [],
            'success': False,
            'total_time': 0,
            'error': None
        }
        
        try:
            # Step 1: Register user
            success, time_taken, token = await self.register_user(user_id)
            results['steps'].append({
                'step': 'register',
                'success': success,
                'time': time_taken,
                'result': 'token_received' if success else token
            })
            
            if not success:
                results['error'] = f"Registration failed: {token}"
                return results
            
            # Step 2: Create DID
            success, time_taken, did = await self.create_did(token, user_id)
            results['steps'].append({
                'step': 'create_did',
                'success': success,
                'time': time_taken,
                'result': did if success else did
            })
            
            if not success:
                results['error'] = f"DID creation failed: {did}"
                return results
            
            # Step 3: Issue credential
            success, time_taken, cred_id = await self.issue_credential(did)
            results['steps'].append({
                'step': 'issue_credential',
                'success': success,
                'time': time_taken,
                'result': cred_id if success else cred_id
            })
            
            if not success:
                results['error'] = f"Credential issuance failed: {cred_id}"
                return results
            
            # Step 4: Verify credential
            success, time_taken, status = await self.verify_credential(cred_id)
            results['steps'].append({
                'step': 'verify_credential',
                'success': success,
                'time': time_taken,
                'result': status if success else status
            })
            
            if not success:
                results['error'] = f"Credential verification failed: {status}"
                return results
            
            results['success'] = True
            
        except Exception as e:
            results['error'] = f"Workflow exception: {str(e)}"
        
        finally:
            results['total_time'] = time.time() - workflow_start
        
        return results
    
    async def run_mixed_load_test(self, duration: int = 60, concurrent_users: int = 5) -> LoadTestMetrics:
        """Run mixed load test with complete workflows"""
        logger.info(f"Starting mixed load test: {concurrent_users} concurrent users for {duration}s")
        
        metrics = LoadTestMetrics()
        start_time = time.time()
        end_time = start_time + duration
        
        # Create semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(concurrent_users)
        
        async def worker(worker_id: int):
            """Worker function to run workflows"""
            user_counter = 0
            while time.time() < end_time:
                async with semaphore:
                    user_id = f"{worker_id}_{user_counter}"
                    workflow_start = time.time()
                    
                    try:
                        result = await self.run_complete_workflow(user_id)
                        workflow_time = time.time() - workflow_start
                        
                        metrics.total_requests += 1
                        metrics.add_response_time(workflow_time)
                        
                        if result['success']:
                            metrics.successful_requests += 1
                        else:
                            metrics.failed_requests += 1
                            error_type = result.get('error', 'unknown_error')[:50]  # Truncate long errors
                            metrics.add_error(error_type)
                        
                        user_counter += 1
                        
                        # Small delay to prevent overwhelming the system
                        await asyncio.sleep(0.1)
                        
                    except Exception as e:
                        workflow_time = time.time() - workflow_start
                        metrics.total_requests += 1
                        metrics.failed_requests += 1
                        metrics.add_response_time(workflow_time)
                        metrics.add_error(f"Worker exception: {str(e)[:50]}")
                        logger.error(f"Worker {worker_id} error: {e}")
        
        # Start all workers
        tasks = [asyncio.create_task(worker(i)) for i in range(concurrent_users)]
        
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Load test error: {e}")
        
        # Calculate final metrics
        metrics.total_duration = time.time() - start_time
        if metrics.total_duration > 0:
            metrics.requests_per_second = metrics.total_requests / metrics.total_duration
        
        metrics.calculate_percentiles()
        
        logger.info(f"Load test completed: {metrics.total_requests} requests, "
                   f"{metrics.successful_requests} successful, "
                   f"{metrics.failed_requests} failed")
        
        return metrics
    
    async def run_single_operation_test(self, operation: str, duration: int = 30, 
                                      concurrent_users: int = 10) -> LoadTestMetrics:
        """Run load test for a single operation type"""
        logger.info(f"Starting {operation} load test: {concurrent_users} concurrent users for {duration}s")
        
        metrics = LoadTestMetrics()
        start_time = time.time()
        end_time = start_time + duration
        
        # Pre-create some test data if needed
        setup_data = {}
        if operation in ['create_did', 'issue_credential', 'verify_credential']:
            # Pre-register a user for other operations
            success, _, token = await self.register_user('setup_user')
            if success:
                setup_data['token'] = token
                if operation in ['issue_credential', 'verify_credential']:
                    success, _, did = await self.create_did(token, 'setup_user')
                    if success:
                        setup_data['did'] = did
                        if operation == 'verify_credential':
                            success, _, cred_id = await self.issue_credential(did)
                            if success:
                                setup_data['credential_id'] = cred_id
        
        semaphore = asyncio.Semaphore(concurrent_users)
        
        async def worker(worker_id: int):
            """Worker function for single operation"""
            counter = 0
            while time.time() < end_time:
                async with semaphore:
                    start_op_time = time.time()
                    
                    try:
                        if operation == 'register':
                            success, op_time, _ = await self.register_user(f"{worker_id}_{counter}")
                        elif operation == 'create_did' and 'token' in setup_data:
                            success, op_time, _ = await self.create_did(setup_data['token'], f"{worker_id}_{counter}")
                        elif operation == 'issue_credential' and 'did' in setup_data:
                            success, op_time, _ = await self.issue_credential(setup_data['did'])
                        elif operation == 'verify_credential' and 'credential_id' in setup_data:
                            success, op_time, _ = await self.verify_credential(setup_data['credential_id'])
                        else:
                            success, op_time = False, 0
                            metrics.add_error("Setup data missing")
                        
                        metrics.total_requests += 1
                        metrics.add_response_time(op_time)
                        
                        if success:
                            metrics.successful_requests += 1
                        else:
                            metrics.failed_requests += 1
                            metrics.add_error(f"{operation}_failed")
                        
                        counter += 1
                        await asyncio.sleep(0.05)  # Smaller delay for single ops
                        
                    except Exception as e:
                        op_time = time.time() - start_op_time
                        metrics.total_requests += 1
                        metrics.failed_requests += 1
                        metrics.add_response_time(op_time)
                        metrics.add_error(f"Exception: {str(e)[:50]}")
        
        # Start workers
        tasks = [asyncio.create_task(worker(i)) for i in range(concurrent_users)]
        
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Single operation test error: {e}")
        
        # Calculate metrics
        metrics.total_duration = time.time() - start_time
        if metrics.total_duration > 0:
            metrics.requests_per_second = metrics.total_requests / metrics.total_duration
        
        metrics.calculate_percentiles()
        
        return metrics

    def _merge_metrics(self, aggregate: LoadTestMetrics, segment: LoadTestMetrics):
        """Merge a segment's metrics into an aggregate metrics object (internal helper)."""
        aggregate.total_requests += segment.total_requests
        aggregate.successful_requests += segment.successful_requests
        aggregate.failed_requests += segment.failed_requests

        # Response-time stats
        aggregate.response_times.extend(segment.response_times)
        aggregate.min_response_time = min(aggregate.min_response_time, segment.min_response_time)
        aggregate.max_response_time = max(aggregate.max_response_time, segment.max_response_time)

        # Errors
        for err, count in segment.errors_by_type.items():
            aggregate.errors_by_type[err] = aggregate.errors_by_type.get(err, 0) + count

    async def run_pattern_load_test(
        self,
        pattern: str = 'ramp',
        total_duration: int = 60,
        base_concurrency: int = 5,
        peak_concurrency: int = 20,
        ramp_steps: int = 5,
        burst_interval: int = 10,
        burst_duration: int = 3
    ) -> LoadTestMetrics:
        """Run a complete-workflow load test using advanced traffic patterns.

        Parameters
        ----------
        pattern : str
            One of ``sustained``, ``burst`` or ``ramp``.
        total_duration : int
            Total run duration in seconds.
        base_concurrency : int
            Concurrency for sustained traffic and low phase in burst/ramp patterns.
        peak_concurrency : int
            Maximum concurrency reached during burst or ramp phases.
        ramp_steps : int
            Number of linear steps when ramping up.
        burst_interval : int
            Interval length (seconds) for burst pattern (high + low phase).
        burst_duration : int
            High-concurrency phase duration (seconds) inside each burst interval.
        """
        if pattern == 'sustained':
            return await self.run_mixed_load_test(duration=total_duration, concurrent_users=base_concurrency)

        metrics = LoadTestMetrics()
        start_time = time.time()

        # Build (duration, concurrency) schedule
        schedule: List[Tuple[int, int]] = []

        if pattern == 'ramp':
            step_duration = max(1, int(total_duration / max(1, ramp_steps)))
            step_increment = max(1, int((peak_concurrency - base_concurrency) / max(1, ramp_steps)))
            current_concurrency = base_concurrency
            elapsed = 0
            while elapsed < total_duration:
                schedule.append((min(step_duration, total_duration - elapsed), current_concurrency))
                current_concurrency = min(current_concurrency + step_increment, peak_concurrency)
                elapsed += step_duration
        elif pattern == 'burst':
            elapsed = 0
            while elapsed < total_duration:
                # High-load segment
                high = min(burst_duration, total_duration - elapsed)
                if high > 0:
                    schedule.append((high, peak_concurrency))
                    elapsed += high
                # Low-load segment
                low = min(burst_interval - burst_duration, total_duration - elapsed)
                if low > 0:
                    schedule.append((low, base_concurrency))
                    elapsed += low
        else:
            raise ValueError(f"Unsupported pattern '{pattern}'.")

        # Execute the schedule sequentially
        for seg_duration, seg_concurrency in schedule:
            seg_metrics = await self.run_mixed_load_test(duration=seg_duration, concurrent_users=seg_concurrency)
            self._merge_metrics(metrics, seg_metrics)

        # Finalise aggregate metrics
        metrics.total_duration = time.time() - start_time
        if metrics.total_duration > 0:
            metrics.requests_per_second = metrics.total_requests / metrics.total_duration
        metrics.calculate_percentiles()
        return metrics


class LoadTestReporter:
    """Generate comprehensive load test reports"""
    
    @staticmethod
    def generate_report(test_type: str, metrics: LoadTestMetrics, 
                       system_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a comprehensive test report"""
        
        # Get system metrics if not provided
        if system_info is None:
            system_info = {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\').percent,
                'network_connections': len(psutil.net_connections())
            }
        
        report = {
            'test_info': {
                'type': test_type,
                'timestamp': datetime.now().isoformat(),
                'duration': metrics.total_duration
            },
            'performance_metrics': metrics.to_dict(),
            'system_metrics': system_info,
            'analysis': LoadTestReporter._analyze_results(metrics),
            'recommendations': LoadTestReporter._generate_recommendations(metrics)
        }
        
        return report
    
    @staticmethod
    def _analyze_results(metrics: LoadTestMetrics) -> Dict[str, Any]:
        """Analyze test results and provide insights"""
        analysis = {
            'performance_grade': 'A',  # Default
            'bottlenecks': [],
            'strengths': [],
            'concerns': []
        }
        
        success_rate = (metrics.successful_requests / max(metrics.total_requests, 1)) * 100
        avg_response = metrics.average_response_time
        
        # Performance grading
        if success_rate >= 99 and avg_response <= 1.0:
            analysis['performance_grade'] = 'A'
        elif success_rate >= 95 and avg_response <= 2.0:
            analysis['performance_grade'] = 'B'
        elif success_rate >= 90 and avg_response <= 5.0:
            analysis['performance_grade'] = 'C'
        elif success_rate >= 80:
            analysis['performance_grade'] = 'D'
        else:
            analysis['performance_grade'] = 'F'
        
        # Identify issues
        if success_rate < 95:
            analysis['concerns'].append(f"Low success rate: {success_rate:.1f}%")
        
        if avg_response > 3.0:
            analysis['bottlenecks'].append(f"High average response time: {avg_response:.2f}s")
        
        if metrics.p95_response_time > 10.0:
            analysis['bottlenecks'].append(f"High P95 response time: {metrics.p95_response_time:.2f}s")
        
        if metrics.requests_per_second < 1.0:
            analysis['bottlenecks'].append(f"Low throughput: {metrics.requests_per_second:.2f} RPS")
        
        # Identify strengths
        if success_rate >= 99:
            analysis['strengths'].append("Excellent reliability")
        
        if avg_response <= 1.0:
            analysis['strengths'].append("Fast response times")
        
        if metrics.requests_per_second >= 10:
            analysis['strengths'].append("High throughput")
        
        return analysis
    
    @staticmethod
    def _generate_recommendations(metrics: LoadTestMetrics) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        success_rate = (metrics.successful_requests / max(metrics.total_requests, 1)) * 100
        
        if success_rate < 90:
            recommendations.append("Investigate error root causes - check service logs")
            recommendations.append("Consider implementing retry mechanisms")
        
        if metrics.average_response_time > 2.0:
            recommendations.append("Optimize database queries and API response times")
            recommendations.append("Consider implementing caching layers")
        
        if metrics.p95_response_time > 5.0:
            recommendations.append("Investigate performance outliers")
            recommendations.append("Consider implementing request timeouts")
        
        if metrics.requests_per_second < 5.0:
            recommendations.append("Scale horizontal infrastructure")
            recommendations.append("Optimize application performance")
        
        if len(metrics.errors_by_type) > 3:
            recommendations.append("Implement better error handling")
            recommendations.append("Add more comprehensive input validation")
        
        if not recommendations:
            recommendations.append("System performing well - monitor for changes")
        
        return recommendations
    
    @staticmethod
    def print_summary(test_type: str, metrics: LoadTestMetrics):
        """Print a concise test summary"""
        success_rate = (metrics.successful_requests / max(metrics.total_requests, 1)) * 100
        
        print(f"\n{'='*60}")
        print(f"LOAD TEST SUMMARY: {test_type}")
        print(f"{'='*60}")
        print(f"Duration: {metrics.total_duration:.1f}s")
        print(f"Total Requests: {metrics.total_requests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Avg Response Time: {metrics.average_response_time:.3f}s")
        print(f"Requests/Second: {metrics.requests_per_second:.2f}")
        print(f"P95 Response Time: {metrics.p95_response_time:.3f}s")
        
        if metrics.errors_by_type:
            print(f"\nTop Errors:")
            for error, count in sorted(metrics.errors_by_type.items(), 
                                     key=lambda x: x[1], reverse=True)[:3]:
                print(f"  - {error}: {count}")
        
        print(f"{'='*60}\n")


# Example usage and testing
async def _demo():
    """Default demo workflow (runs when the script is executed without CLI args)."""
    async with DIDentityLoadTester() as tester:
        print("Running demo load test (30s, 3 concurrent users)...")
        metrics = await tester.run_mixed_load_test(duration=30, concurrent_users=3)
        report = LoadTestReporter.generate_report("Demo Workflow", metrics)
        LoadTestReporter.print_summary("Demo Workflow", metrics)
        with open(f'load_test_report_{int(time.time())}.json', 'w') as f:
            json.dump(report, f, indent=2)


def _build_arg_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser for the load-testing suite."""
    parser = argparse.ArgumentParser(description="DIDentity Load Testing CLI")
    parser.add_argument('--pattern', choices=['sustained', 'burst', 'ramp'], default='sustained',
                        help='Traffic pattern to use (complete workflow only)')
    parser.add_argument('--operation', choices=['workflow', 'register', 'create_did',
                                                'issue_credential', 'verify_credential'],
                        default='workflow', help='Which operation to test')
    parser.add_argument('--duration', type=int, default=60, help='Total test duration in seconds')
    parser.add_argument('--concurrent-users', type=int, default=5,
                        help='Base concurrency / sustained concurrency level')
    parser.add_argument('--peak-concurrency', type=int, default=20,
                        help='Peak concurrency for ramp/burst patterns')
    parser.add_argument('--ramp-steps', type=int, default=5,
                        help='Number of steps when using the ramp pattern')
    parser.add_argument('--burst-interval', type=int, default=10,
                        help='Full interval length (seconds) for the burst pattern')
    parser.add_argument('--burst-duration', type=int, default=3,
                        help='High-load duration (seconds) inside each burst interval')
    parser.add_argument('-o', '--output', help='Path to write the detailed JSON report')
    return parser


async def _run_cli(args):
    """Execute the load test according to parsed CLI arguments."""
    async with DIDentityLoadTester() as tester:
        if args.operation != 'workflow':
            metrics = await tester.run_single_operation_test(
                operation=args.operation,
                duration=args.duration,
                concurrent_users=args.concurrent_users
            )
            test_name = f"Single Operation ({args.operation})"
        else:
            if args.pattern == 'sustained':
                metrics = await tester.run_mixed_load_test(
                    duration=args.duration,
                    concurrent_users=args.concurrent_users
                )
            else:
                metrics = await tester.run_pattern_load_test(
                    pattern=args.pattern,
                    total_duration=args.duration,
                    base_concurrency=args.concurrent_users,
                    peak_concurrency=args.peak_concurrency,
                    ramp_steps=args.ramp_steps,
                    burst_interval=args.burst_interval,
                    burst_duration=args.burst_duration
                )
            test_name = f"Complete Workflow ({args.pattern})"

        report = LoadTestReporter.generate_report(test_name, metrics)
        LoadTestReporter.print_summary(test_name, metrics)
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)


def _prompt_int(prompt: str, default: int) -> int:
    """Helper to prompt for an int with default."""
    while True:
        try:
            val = input(f"{prompt} [{default}]: ") or str(default)
            return int(val)
        except ValueError:
            print("Please enter a valid integer.")


def _interactive_prompt() -> argparse.Namespace:
    """Launch textual wizard to collect load-test parameters from the user."""
    print("\n===== DIDentity Load-Testing Interactive Wizard =====\n")
    workflow = input("Choose test type (workflow / single): [workflow] ") or "workflow"
    workflow = workflow.strip().lower()

    if workflow == 'single':
        operation = input("Select operation (register / create_did / issue_credential / verify_credential): [register] ") or "register"
        duration = _prompt_int("Test duration in seconds", 60)
        concurrency = _prompt_int("Concurrent users", 5)
        args = SimpleNamespace(
            pattern='sustained',  # not used
            operation=operation,
            duration=duration,
            concurrent_users=concurrency,
            peak_concurrency=None,
            ramp_steps=None,
            burst_interval=None,
            burst_duration=None,
            output=input("Output JSON file (leave blank to skip): ") or None
        )
        return args

    # Complete workflow path
    pattern = input("Traffic pattern (sustained / burst / ramp): [sustained] ") or "sustained"
    pattern = pattern.strip().lower()

    duration = _prompt_int("Total test duration in seconds", 60)
    base_concurrency = _prompt_int("Base concurrency", 5)

    # pattern-specific extras
    peak = base_concurrency
    ramp_steps = 5
    burst_interval = 10
    burst_duration = 3
    if pattern in ('ramp', 'burst'):
        peak = _prompt_int("Peak concurrency", max(base_concurrency * 2, 10))
    if pattern == 'ramp':
        ramp_steps = _prompt_int("Number of ramp steps", 5)
    elif pattern == 'burst':
        burst_interval = _prompt_int("Burst interval length (seconds)", 10)
        burst_duration = _prompt_int("High-load duration inside each burst (seconds)", 3)

    args = SimpleNamespace(
        pattern=pattern,
        operation='workflow',
        duration=duration,
        concurrent_users=base_concurrency,
        peak_concurrency=peak,
        ramp_steps=ramp_steps,
        burst_interval=burst_interval,
        burst_duration=burst_duration,
        output=input("Output JSON file (leave blank to skip): ") or None
    )
    return args


def main():
    """Entry-point wrapper that decides whether to run the demo or the CLI."""
    if len(sys.argv) == 1 and sys.stdin.isatty():
        # Interactive wizard
        args = _interactive_prompt()
        asyncio.run(_run_cli(args))
    else:
        parser = _build_arg_parser()
        args = parser.parse_args()
        asyncio.run(_run_cli(args))


if __name__ == "__main__":
    main() 