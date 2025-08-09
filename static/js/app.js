document.addEventListener('DOMContentLoaded', function() {
const tg = window.Telegram.WebApp;
tg.expand();

function getCurrentDateUTC4() {
    const date = new Date();
    return date;
}

let currentDate = getCurrentDateUTC4();
let selectedGroupId = null;
let selectedTeacherName = null;
let currentMode = 'groups'; // 'groups' или 'teachers'
let groupMap = {};

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
    let headerText = '';
    if (schedule && schedule.date) {
        headerText = schedule.date;
    } else {
        const days = ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота'];
        const day = selectedDate.getDate().toString().padStart(2, '0');
        const month = (selectedDate.getMonth() + 1).toString().padStart(2, '0');
        const year = selectedDate.getFullYear();
        headerText = `${days[selectedDate.getDay()]} ${day}.${month}.${year}`;
    }
    // Добавляем название группы или ФИО преподавателя
    if (currentMode === 'groups' && selectedGroupId && groupMap[selectedGroupId]) {
        headerText += ' — ' + groupMap[selectedGroupId];
    } else if (currentMode === 'teachers' && selectedTeacherName) {
        headerText += ' — ' + selectedTeacherName;
    }
    dayHeader.textContent = headerText;
    container.appendChild(dayHeader);

    if (schedule && schedule.lessons && schedule.lessons.length > 0) {
        schedule.lessons
            .sort((a, b) => a.time.localeCompare(b.time))
            .forEach(lesson => {
                const lessonBlock = document.createElement('div');
                lessonBlock.className = 'lesson-block';
                let detailsHtml = `${lesson.type}<br>Аудитория: ${lesson.classroom}<br>`;
                if (currentMode === 'groups') {
                    // Преподаватель кликабелен
                    detailsHtml += `Преподаватель: <a href="#" class="teacher-link" data-teacher="${encodeURIComponent(lesson.teacher)}">${lesson.teacher}</a>`;
                } else if (currentMode === 'teachers') {
                    // Группа кликабельна (если есть)
                    if (lesson.group_id && groupMap[lesson.group_id]) {
                        detailsHtml += `Группа: <a href="#" class="group-link" data-group="${lesson.group_id}">${groupMap[lesson.group_id]}</a><br>`;
                    }
                    detailsHtml += `Преподаватель: ${lesson.teacher}`;
                } else {
                    detailsHtml += `Преподаватель: ${lesson.teacher}`;
                }
                lessonBlock.innerHTML = `
                    <div class="time-slot">${lesson.time}</div>
                    <div class="subject">${lesson.subject}</div>
                    <div class="details">${detailsHtml}</div>
                `;
                container.appendChild(lessonBlock);
            });
        // Добавляем обработчики клика по преподавателю
        container.querySelectorAll('.teacher-link').forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const teacher = decodeURIComponent(this.getAttribute('data-teacher'));
                if (teacher) {
                    selectedTeacherName = teacher;
                    selectedGroupId = null;
                    currentMode = 'teachers';
                    document.getElementById('teachersBtn').classList.add('active');
                    document.getElementById('groupsBtn').classList.remove('active');
                    loadTeachers(teacher);
                    loadSchedule();
                }
            });
        });
        // Добавляем обработчики клика по группе
        container.querySelectorAll('.group-link').forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const groupId = this.getAttribute('data-group');
                if (groupId) {
                    selectedGroupId = groupId;
                    selectedTeacherName = null;
                    currentMode = 'groups';
                    document.getElementById('groupsBtn').classList.add('active');
                    document.getElementById('teachersBtn').classList.remove('active');
                    loadGroups(groupId);
                    loadSchedule();
                }
            });
        });
    } else {
        container.innerHTML += '<div class="empty-schedule">Нет занятий в этот день</div>';
    }
}

// Вспомогательная функция для fetch с initData
async function fetchWithInitData(url, options = {}) {
    const tg = window.Telegram.WebApp;
    const initData = tg && tg.initData ? tg.initData : '';
    const commonHeaders = {
        'X-Telegram-InitData': initData,
        'Telegram-Init-Data': initData,
        'X-Telegram-Web-App-Data': initData
    };
    if (!options.method || options.method.toUpperCase() === 'GET') {
        options.headers = Object.assign({}, options.headers || {}, commonHeaders);
        const resp = await fetch(url, options);
        if (resp.status === 401) await showOpenInTelegram();
        return resp;
    } else {
        let body = options.body ? JSON.parse(options.body) : {};
        body.initData = initData;
        options.body = JSON.stringify(body);
        options.headers = Object.assign({}, options.headers || {}, { 'Content-Type': 'application/json' }, commonHeaders);
        const resp = await fetch(url, options);
        if (resp.status === 401) await showOpenInTelegram();
        return resp;
    }
}

async function showOpenInTelegram() {
    try {
        const cfg = await fetch('/config-public').then(r => r.json());
        const uname = cfg.bot_username;
        if (!uname) return;
        const container = document.getElementById('scheduleContainer');
        container.innerHTML = '';
        const div = document.createElement('div');
        div.className = 'empty-schedule';
        div.innerHTML = `Авторизация через Telegram не пройдена.<br/>Откройте мини‑приложение через бота:<br/><a href="https://t.me/${uname}?startapp=go" target="_blank">Открыть в Telegram</a>`;
        container.appendChild(div);
    } catch (e) {}
}

async function loadGroups(selectedId = null) {
    try {
        const response = await fetchWithInitData('/groups/');
        if (response.ok) {
            const groups = await response.json();
            groupMap = {};
            const select = document.getElementById('groupSelect');
            select.innerHTML = '<option value="">Выберите группу</option>';
            groups.forEach(group => {
                groupMap[group.id] = group.name;
                const option = document.createElement('option');
                option.value = group.id;
                option.textContent = group.name;
                select.appendChild(option);
            });
            // Установить выбранное значение, если передано
            if (selectedId) {
                select.value = selectedId;
            } else if (selectedGroupId) {
                select.value = selectedGroupId;
            }
        }
    } catch (error) {
        console.error('Ошибка загрузки групп:', error);
    }
}

async function loadTeachers(selectedName = null) {
    try {
        const response = await fetchWithInitData('/teachers/');
        if (response.ok) {
            const teachers = await response.json();
            const select = document.getElementById('groupSelect');
            select.innerHTML = '<option value="">Выберите преподавателя</option>';
            teachers.forEach(teacher => {
                const option = document.createElement('option');
                option.value = teacher.name;
                option.textContent = teacher.name;
                select.appendChild(option);
            });
            // Установить выбранное значение, если передано
            if (selectedName) {
                select.value = selectedName;
            } else if (selectedTeacherName) {
                select.value = selectedTeacherName;
            }
        }
    } catch (error) {
        console.error('Ошибка загрузки преподавателей:', error);
    }
}

async function loadLastSelection() {
    try {
        const resp = await fetchWithInitData('/user/selection');
        if (!resp.ok) return;
        const data = await resp.json();
        if (data.last_selected_group_id) {
            selectedGroupId = String(data.last_selected_group_id);
            currentMode = 'groups';
            document.getElementById('groupsBtn').classList.add('active');
            document.getElementById('teachersBtn').classList.remove('active');
            await loadGroups(selectedGroupId);
            await loadSchedule();
        } else if (data.last_selected_teacher) {
            selectedTeacherName = data.last_selected_teacher;
            currentMode = 'teachers';
            document.getElementById('teachersBtn').classList.add('active');
            document.getElementById('groupsBtn').classList.remove('active');
            await loadTeachers(selectedTeacherName);
            await loadSchedule();
        }
    } catch (e) {}
}

async function saveLastSelection() {
    try {
        const body = {};
        if (selectedGroupId) body.group_id = Number(selectedGroupId);
        if (selectedTeacherName) body.teacher = selectedTeacherName;
        await fetchWithInitData('/user/selection', { method: 'POST', body: JSON.stringify(body) });
    } catch (e) {}
}

function setMode(mode) {
    currentMode = mode;
    const groupsBtn = document.getElementById('groupsBtn');
    const teachersBtn = document.getElementById('teachersBtn');
    if (mode === 'groups') {
        groupsBtn.classList.add('active');
        teachersBtn.classList.remove('active');
        loadGroups();
        selectedTeacherName = null;
    } else {
        teachersBtn.classList.add('active');
        groupsBtn.classList.remove('active');
        loadTeachers();
        selectedGroupId = null;
    }
    // Сбросить выбранное значение
    document.getElementById('groupSelect').value = '';
}

async function loadSchedule() {
    if (currentMode === 'groups') {
        if (!selectedGroupId) return;
    } else {
        if (!selectedTeacherName) return;
    }

    const adjustedDate = new Date(currentDate);
    adjustedDate.setDate(adjustedDate.getDate() + 1);
    const dateStr = adjustedDate.toISOString().split('T')[0];

    try {
        let response;
        if (currentMode === 'groups') {
            response = await fetchWithInitData(`/groups/${selectedGroupId}/schedule/${dateStr}`);
        } else {
            // encodeURIComponent для ФИО
            response = await fetchWithInitData(`/teachers/${encodeURIComponent(selectedTeacherName)}/schedule/${dateStr}`);
        }
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

async function showUserInfo() {
    const el = document.getElementById('userInfo');
    try {
        const resp = await fetchWithInitData('/whoami');
        if (!resp.ok) throw new Error('unauth');
        const data = await resp.json();
        const uid = data.user_id || '—';
        const uname = data.username ? '@'+data.username : '';
        el.textContent = `Ваш ID: ${uid} ${uname}`;
    } catch (e) {
        el.innerHTML = 'Откройте через бота, чтобы авторизоваться';
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
document.getElementById('groupSelect').addEventListener('change', async (e) => {
    if (currentMode === 'groups') {
        selectedGroupId = e.target.value;
        selectedTeacherName = null;
    } else {
        selectedTeacherName = e.target.value;
        selectedGroupId = null;
    }
    if (selectedGroupId || selectedTeacherName) {
        await saveLastSelection();
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

document.getElementById('groupsBtn').addEventListener('click', () => setMode('groups'));
document.getElementById('teachersBtn').addEventListener('click', () => setMode('teachers'));

// Инициализация
(async function initApp(){
    tg.ready();
    updateTodayDate();
    await loadGroups();
    initDatePicker();
    await loadLastSelection();
    await showUserInfo();
})(); 
});
