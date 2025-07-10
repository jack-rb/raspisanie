const tg = window.Telegram.WebApp;
tg.expand();

let selectedDate = new Date();
let currentSearchType = 'group'; // 'group' или 'teacher'

function formatDate(date, isToday = false) {
    const days = ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота'];
    const day = days[date.getDay()];
    const dd = String(date.getDate()).padStart(2, '0');
    const mm = String(date.getMonth() + 1).padStart(2, '0');
    const yyyy = date.getFullYear();
    
    if (isToday) {
        return `${day}, ${dd}.${mm}.${yyyy}`;
    }
    // Для API возвращаем формат YYYY-MM-DD
    return `${yyyy}-${mm}-${dd}`;
}

function updateTodayDate() {
    const todayElement = document.getElementById('todayDate');
    const today = new Date();
    const days = ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота'];
    const day = days[today.getDay()];
    const dd = String(today.getDate()).padStart(2, '0');
    const mm = String(today.getMonth() + 1).padStart(2, '0');
    const yyyy = today.getFullYear();
    todayElement.textContent = `${day}, ${dd}.${mm}.${yyyy}`;
}

function updateCurrentTime() {
    const timeElement = document.getElementById('currentTime');
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    timeElement.textContent = `${hours}:${minutes}:${seconds}`;
}

function displaySchedule(schedule, selectedDate) {
    const container = document.getElementById('scheduleContainer');
    container.innerHTML = '';

    const dayHeader = document.createElement('div');
    dayHeader.className = 'day-header';
    
    // Всегда показываем дату в нужном формате
    const days = ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота'];
    const day = selectedDate.getDate().toString().padStart(2, '0');
    const month = (selectedDate.getMonth() + 1).toString().padStart(2, '0');
    const year = selectedDate.getFullYear();
    dayHeader.textContent = `${days[selectedDate.getDay()]} ${day}.${month}.${year}`;
    
    // Добавляем информацию о преподавателе, если это расписание преподавателя
    if (schedule && schedule.teacher) {
        const teacherInfo = document.createElement('div');
        teacherInfo.className = 'teacher-info';
        teacherInfo.textContent = `Преподаватель: ${schedule.teacher}`;
        container.appendChild(teacherInfo);
    }
    
    container.appendChild(dayHeader);

    if (schedule && schedule.lessons && schedule.lessons.length > 0) {
        schedule.lessons
            .sort((a, b) => a.time.localeCompare(b.time))
            .forEach(lesson => {
                const lessonBlock = document.createElement('div');
                lessonBlock.className = 'lesson-block';
                
                // Формируем детали в зависимости от типа поиска
                let details = `${lesson.type}<br>Аудитория: ${lesson.classroom}`;
                
                if (currentSearchType === 'teacher') {
                    // Для расписания преподавателя показываем кликабельную группу
                    details += `<br>Группа: <span class="clickable" data-type="group" data-value="${lesson.group_name}">${lesson.group_name}</span>`;
                } else {
                    // Для расписания группы показываем кликабельного преподавателя
                    details += `<br>Преподаватель: <span class="clickable" data-type="teacher" data-value="${lesson.teacher}">${lesson.teacher}</span>`;
                }
                
                lessonBlock.innerHTML = `
                    <div class="time-slot">${lesson.time}</div>
                    <div class="subject">${lesson.subject}</div>
                    <div class="details">${details}</div>
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

async function loadSchedule(groupId, date) {
    const formattedDate = formatDate(date);
    
    try {
        const response = await fetch(`/schedule/${groupId}/${formattedDate}`);
        if (response.ok) {
            const schedule = await response.json();
            displaySchedule(schedule, date);
        } else {
            displaySchedule(null, date);
        }
    } catch (error) {
        console.error('Ошибка загрузки расписания:', error);
        displaySchedule(null, date);
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
    dayWheel.value = selectedDate.getDate();
    
    const months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 
                   'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
    months.forEach((month, i) => {
        const option = document.createElement('option');
        option.value = i + 1;
        option.text = month;
        monthWheel.appendChild(option);
    });
    monthWheel.value = selectedDate.getMonth() + 1;
    
    const currentYear = today.getFullYear();
    for (let year = currentYear - 1; year <= currentYear + 1; year++) {
        const option = document.createElement('option');
        option.value = year;
        option.text = year.toString();
        yearWheel.appendChild(option);
    }
    yearWheel.value = selectedDate.getFullYear();
}

function showDatePicker() {
    document.getElementById('datePickerModal').style.display = 'block';
}

function hideDatePicker() {
    document.getElementById('datePickerModal').style.display = 'none';
}

function confirmDateSelection() {
    const day = document.getElementById('dayWheel').value;
    const month = document.getElementById('monthWheel').value;
    const year = document.getElementById('yearWheel').value;
    
    selectedDate = new Date(year, month - 1, day);
    
    updateSchedule();
    hideDatePicker();
}

document.addEventListener('DOMContentLoaded', function() {
    loadGroups();
    updateTodayDate();
    updateCurrentTime();
    setupEventListeners();
    
    // Обновляем время каждую секунду
    setInterval(updateCurrentTime, 1000);
});

function setupEventListeners() {
    // Кнопки переключения типа поиска
    document.getElementById('searchByGroup').addEventListener('click', () => switchSearchType('group'));
    document.getElementById('searchByTeacher').addEventListener('click', () => switchSearchType('teacher'));
    
    // Выбор группы или преподавателя
    document.getElementById('groupSelect').addEventListener('change', function() {
        if (this.value) {
            if (currentSearchType === 'group') {
                loadSchedule(this.value, selectedDate);
            } else {
                loadScheduleByTeacher(this.value, selectedDate);
            }
        }
    });
    
    // Обработчик кликов по кликабельным элементам
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('clickable')) {
            const type = e.target.dataset.type;
            const value = e.target.dataset.value;
            
            if (type === 'teacher') {
                // Переключаемся на поиск по преподавателю
                switchSearchType('teacher');
                // Находим преподавателя в списке и выбираем его
                setTimeout(() => {
                    const select = document.getElementById('groupSelect');
                    const options = Array.from(select.options);
                    const teacherOption = options.find(option => option.textContent === value);
                    if (teacherOption) {
                        select.value = teacherOption.value;
                        loadScheduleByTeacher(teacherOption.value, selectedDate);
                    }
                }, 100);
            } else if (type === 'group') {
                // Переключаемся на поиск по группе
                switchSearchType('group');
                // Находим группу в списке и выбираем её
                setTimeout(() => {
                    const select = document.getElementById('groupSelect');
                    const options = Array.from(select.options);
                    const groupOption = options.find(option => option.textContent === value);
                    if (groupOption) {
                        select.value = groupOption.value;
                        loadSchedule(groupOption.value, selectedDate);
                    }
                }, 100);
            }
        }
    });
    
    // Навигация по дням
    document.getElementById('prev-day').addEventListener('click', () => {
        selectedDate.setDate(selectedDate.getDate() - 1);
        updateSchedule();
    });
    
    document.getElementById('next-day').addEventListener('click', () => {
        selectedDate.setDate(selectedDate.getDate() + 1);
        updateSchedule();
    });
    
    // Выбор даты
    document.getElementById('date-picker').addEventListener('click', showDatePicker);
    document.getElementById('confirmDate').addEventListener('click', confirmDateSelection);
    document.getElementById('cancelDate').addEventListener('click', hideDatePicker);
}

function switchSearchType(type) {
    currentSearchType = type;
    
    // Обновляем активную кнопку
    document.getElementById('searchByGroup').classList.toggle('active', type === 'group');
    document.getElementById('searchByTeacher').classList.toggle('active', type === 'teacher');
    
    // Обновляем содержимое выпадающего списка
    updateSelectContent(type);
    
    // Очищаем расписание при переключении
    document.getElementById('scheduleContainer').innerHTML = '';
    
    // Сбрасываем выбор
    document.getElementById('groupSelect').value = '';
}

function updateSelectContent(type) {
    const select = document.getElementById('groupSelect');
    
    if (type === 'group') {
        // Загружаем группы
        loadGroups();
        select.placeholder = 'Выберите группу';
    } else {
        // Загружаем преподавателей
        loadTeachers();
        select.placeholder = 'Выберите преподавателя';
    }
}

function updateSchedule() {
    const selectedId = document.getElementById('groupSelect').value;
    if (selectedId) {
        if (currentSearchType === 'group') {
            loadSchedule(selectedId, selectedDate);
        } else {
            loadScheduleByTeacher(selectedId, selectedDate);
        }
    }
}

function loadScheduleByTeacher(teacherId, date) {
    const formattedDate = formatDate(date);
    fetch(`/schedule/teacher/${teacherId}/${formattedDate}`)
        .then(response => response.json())
        .then(schedule => {
            displaySchedule(schedule, date);
        })
        .catch(error => {
            console.error('Ошибка загрузки расписания преподавателя:', error);
            document.getElementById('scheduleContainer').innerHTML = 
                '<div class="empty-schedule">Ошибка загрузки расписания</div>';
        });
}

function loadTeachers() {
    fetch('/teachers/')
        .then(response => response.json())
        .then(teachers => {
            const select = document.getElementById('groupSelect');
            select.innerHTML = '<option value="">Выберите преподавателя</option>';
            teachers.forEach(teacher => {
                const option = document.createElement('option');
                option.value = teacher.id;
                option.textContent = teacher.name;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Ошибка загрузки преподавателей:', error);
        });
}

// Инициализация
tg.ready();

// Добавляем initData в заголовки для всех запросов
const originalFetch = window.fetch;
window.fetch = function(url, options = {}) {
    if (tg.initData) {
        options.headers = {
            ...options.headers,
            'X-Telegram-Init-Data': tg.initData
        };
    }
    return originalFetch(url, options);
};

initDatePicker(); 