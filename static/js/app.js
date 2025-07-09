const tg = window.Telegram.WebApp;
tg.expand();

function getCurrentDateUTC4() {
    const date = new Date();
    return date;
}

let currentDate = getCurrentDateUTC4();
let selectedGroupId = null;

function formatDate(date, isToday = false) {
    const days = ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота'];
    const day = days[date.getDay()];
    const dd = String(date.getDate()).padStart(2, '0');
    const mm = String(date.getMonth() + 1).padStart(2, '0');
    const yyyy = date.getFullYear();
    
    if (isToday) {
        return `${day}, ${dd}.${mm}.${yyyy}`;
    }
    return `${day} ${dd}.${mm}.${yyyy}`;
}

function updateTodayDate() {
    const todayElement = document.getElementById('todayDate');
    todayElement.textContent = formatDate(getCurrentDateUTC4(), true);
}

function displaySchedule(schedule, selectedDate) {
    const container = document.getElementById('scheduleContainer');
    container.innerHTML = '';

    const dayHeader = document.createElement('div');
    dayHeader.className = 'day-header';
    
    if (schedule && schedule.date) {
        dayHeader.textContent = schedule.date;
    } else {
        const days = ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота'];
        const day = selectedDate.getDate().toString().padStart(2, '0');
        const month = (selectedDate.getMonth() + 1).toString().padStart(2, '0');
        const year = selectedDate.getFullYear();
        dayHeader.textContent = `${days[selectedDate.getDay()]} ${day}.${month}.${year}`;
    }
    container.appendChild(dayHeader);

    if (schedule && schedule.lessons && schedule.lessons.length > 0) {
        schedule.lessons
            .sort((a, b) => a.time.localeCompare(b.time))
            .forEach(lesson => {
                const lessonBlock = document.createElement('div');
                lessonBlock.className = 'lesson-block';
                lessonBlock.innerHTML = `
                    <div class="time-slot">${lesson.time}</div>
                    <div class="subject">${lesson.subject}</div>
                    <div class="details">
                        ${lesson.type}<br>
                        Аудитория: ${lesson.classroom}<br>
                        Преподаватель: ${lesson.teacher}
                    </div>
                `;
                container.appendChild(lessonBlock);
            });
    } else {
        container.innerHTML += '<div class="empty-schedule">Нет занятий в этот день</div>';
    }
}

async function loadGroups() {
    try {
        const response = await fetch('/groups/');
        if (response.ok) {
            const groups = await response.json();
            const select = document.getElementById('groupSelect');
            select.innerHTML = '<option value="">Выберите группу</option>';
            groups.forEach(group => {
                const option = document.createElement('option');
                option.value = group.id;
                option.textContent = group.name;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Ошибка загрузки групп:', error);
    }
}

async function loadSchedule() {
    if (!selectedGroupId) return;

    const adjustedDate = new Date(currentDate);
    adjustedDate.setDate(adjustedDate.getDate() + 1);
    const dateStr = adjustedDate.toISOString().split('T')[0];

    try {
        const response = await fetch(`/groups/${selectedGroupId}/schedule/${dateStr}`);
        if (response.ok) {
            const schedule = await response.json();
            displaySchedule(schedule, currentDate);
        } else {
            displaySchedule(null, currentDate);
        }
    } catch (error) {
        console.error('Ошибка загрузки расписания:', error);
        displaySchedule(null, currentDate);
    }
}

function initDatePicker() {
    const dayWheel = document.getElementById('dayWheel');
    const monthWheel = document.getElementById('monthWheel');
    const yearWheel = document.getElementById('yearWheel');
    
    const today = new Date();
    
    for (let i = 1; i <= 31; i++) {
        const option = document.createElement('option');
        option.value = i;
        option.text = i.toString().padStart(2, '0');
        dayWheel.appendChild(option);
    }
    dayWheel.value = today.getDate();
    
    const months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 
                   'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
    months.forEach((month, i) => {
        const option = document.createElement('option');
        option.value = i + 1;
        option.text = month;
        monthWheel.appendChild(option);
    });
    monthWheel.value = today.getMonth() + 1;
    
    const currentYear = today.getFullYear();
    for (let year = currentYear - 1; year <= currentYear + 1; year++) {
        const option = document.createElement('option');
        option.value = year;
        option.text = year.toString();
        yearWheel.appendChild(option);
    }
    yearWheel.value = currentYear;
}

// Event Listeners
document.getElementById('groupSelect').addEventListener('change', (e) => {
    selectedGroupId = e.target.value;
    if (selectedGroupId) {
        loadSchedule();
    }
});

document.getElementById('prev-day').addEventListener('click', () => {
    currentDate.setDate(currentDate.getDate() - 1);
    loadSchedule();
});

document.getElementById('next-day').addEventListener('click', () => {
    currentDate.setDate(currentDate.getDate() + 1);
    loadSchedule();
});

document.getElementById('date-picker').addEventListener('click', () => {
    document.getElementById('datePickerModal').style.display = 'block';
});

document.getElementById('cancelDate').addEventListener('click', () => {
    document.getElementById('datePickerModal').style.display = 'none';
});

document.getElementById('confirmDate').addEventListener('click', () => {
    const day = document.getElementById('dayWheel').value;
    const month = document.getElementById('monthWheel').value;
    const year = document.getElementById('yearWheel').value;
    
    currentDate = new Date(year, month - 1, day);
    
    const dayHeader = document.createElement('div');
    dayHeader.className = 'day-header';
    
    const days = ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота'];
    const dayName = days[currentDate.getDay()];
    const formattedDate = `${dayName} ${day.padStart(2, '0')}.${month.padStart(2, '0')}.${year}`;
    dayHeader.textContent = formattedDate;
    
    const container = document.getElementById('scheduleContainer');
    container.innerHTML = '';
    container.appendChild(dayHeader);
    
    loadSchedule();
    
    document.getElementById('datePickerModal').style.display = 'none';
});

// Инициализация
tg.ready();
updateTodayDate();
loadGroups();
initDatePicker(); 