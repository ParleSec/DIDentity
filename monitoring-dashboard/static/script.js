// Tab switching functionality
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });
    
    // Show selected tab
    const selectedTab = document.getElementById(tabName + '-tab');
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // Mark button as active
    const clickedButton = event.target;
    if (clickedButton) {
        clickedButton.classList.add('active');
    }
}

// Auto-refresh functionality
let refreshTimer = 30;
const timerDisplay = document.getElementById('refresh-timer');

if (timerDisplay) {
    setInterval(() => {
        refreshTimer--;
        timerDisplay.textContent = refreshTimer;
        
        if (refreshTimer <= 0) {
            location.reload();
        }
    }, 1000);

    // Auto-refresh every 30 seconds
    setTimeout(() => {
        location.reload();
    }, 30000);
}