// Test if JavaScript is running
console.log('Calendar script starting...');

// Wait for DOM to be fully loaded
window.onload = function() {
    console.log('Window loaded');
    try {
        const debugInfo = document.getElementById('debugInfo');
        if (!debugInfo) {
            console.error('Debug info element not found');
            return;
        }
        debugInfo.textContent = 'Window loaded\n';

        // Test if DOM elements are accessible
        const currentMonth = document.getElementById('currentMonth');
        const calendarGrid = document.getElementById('calendarGrid');
        
        if (!currentMonth || !calendarGrid) {
            debugInfo.textContent += 'Error: Required DOM elements not found\n';
            console.error('Required DOM elements not found');
            return;
        }

        debugInfo.textContent += 'DOM elements found: currentMonth yes, calendarGrid yes\n';

        let currentDate = new Date();

        function logDebug(message) {
            console.log(message);
            debugInfo.textContent += message + '\n';
        }

        function renderCalendar() {
            logDebug('Rendering calendar...');
            const year = currentDate.getFullYear();
            const month = currentDate.getMonth();
            
            // Update month display
            const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 
                             'July', 'August', 'September', 'October', 'November', 'December'];
            currentMonth.textContent = `${monthNames[month]} ${year}`;
            
            // Create calendar grid
            const firstDay = new Date(year, month, 1);
            const lastDay = new Date(year, month + 1, 0);
            const startingDay = firstDay.getDay();
            const totalDays = lastDay.getDate();
            
            logDebug(`Calendar parameters: year=${year}, month=${month}, startingDay=${startingDay}, totalDays=${totalDays}`);
            
            // Clear and create grid
            calendarGrid.innerHTML = '';
            
            // Add day headers
            const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
            days.forEach(day => {
                const dayHeader = document.createElement('div');
                dayHeader.style.textAlign = 'center';
                dayHeader.style.fontWeight = 'bold';
                dayHeader.style.padding = '5px';
                dayHeader.style.backgroundColor = '#f8f9fa';
                dayHeader.textContent = day;
                calendarGrid.appendChild(dayHeader);
            });
            
            // Add empty cells for days before the first of the month
            for (let i = 0; i < startingDay; i++) {
                const emptyDay = document.createElement('div');
                emptyDay.style.border = '1px solid #dee2e6';
                emptyDay.style.padding = '10px';
                emptyDay.style.minHeight = '100px';
                emptyDay.style.backgroundColor = '#f8f9fa';
                calendarGrid.appendChild(emptyDay);
            }
            
            // Add days of the month
            const today = new Date();
            for (let day = 1; day <= totalDays; day++) {
                const dayElement = document.createElement('div');
                dayElement.style.border = '1px solid #dee2e6';
                dayElement.style.padding = '10px';
                dayElement.style.minHeight = '100px';
                dayElement.style.backgroundColor = 'white';
                
                // Check if this is today
                if (year === today.getFullYear() && month === today.getMonth() && day === today.getDate()) {
                    dayElement.style.backgroundColor = '#e9ecef';
                }
                
                // Add day number
                dayElement.textContent = day;
                calendarGrid.appendChild(dayElement);
            }
            
            logDebug('Calendar rendered');
        }

        // Make these functions globally available
        window.prevMonth = function() {
            currentDate.setMonth(currentDate.getMonth() - 1);
            renderCalendar();
        };

        window.nextMonth = function() {
            currentDate.setMonth(currentDate.getMonth() + 1);
            renderCalendar();
        };

        // Initial render
        renderCalendar();
        logDebug('Calendar initialization complete');

    } catch (error) {
        console.error('Error in calendar initialization:', error);
        const debugInfo = document.getElementById('debugInfo');
        if (debugInfo) {
            debugInfo.textContent += 'Error: ' + error.message + '\n';
        }
    }
}; 