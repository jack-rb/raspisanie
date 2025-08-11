// Календарь расписания ПГУТИ
class ScheduleCalendar {
    constructor() {
        this.currentDate = new Date();
        this.currentMonth = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth(), 1);
        this.init();
    }

    init() {
        this.renderCalendar();
        this.bindEvents();
        this.updateQuickLinks();
    }

    bindEvents() {
        document.getElementById('prevMonth').addEventListener('click', () => {
            this.currentMonth.setMonth(this.currentMonth.getMonth() - 1);
            this.renderCalendar();
        });

        document.getElementById('nextMonth').addEventListener('click', () => {
            this.currentMonth.setMonth(this.currentMonth.getMonth() + 1);
            this.renderCalendar();
        });
    }

    renderCalendar() {
        const grid = document.getElementById('calendarGrid');
        const monthDisplay = document.getElementById('currentMonth');
        
        // Обновляем заголовок месяца
        const monthNames = [
            'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
            'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
        ];
        monthDisplay.textContent = `${monthNames[this.currentMonth.getMonth()]} ${this.currentMonth.getFullYear()}`;

        // Очищаем календарь
        grid.innerHTML = '';

        // Добавляем заголовки дней недели
        const dayNames = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
        dayNames.forEach(day => {
            const dayHeader = document.createElement('div');
            dayHeader.className = 'calendar-day-header';
            dayHeader.textContent = day;
            grid.appendChild(dayHeader);
        });

        // Получаем первый день месяца и количество дней
        const firstDay = new Date(this.currentMonth.getFullYear(), this.currentMonth.getMonth(), 1);
        const lastDay = new Date(this.currentMonth.getFullYear(), this.currentMonth.getMonth() + 1, 0);
        const daysInMonth = lastDay.getDate();
        
        // Получаем день недели первого дня (0 = воскресенье, 1 = понедельник, ...)
        let firstDayOfWeek = firstDay.getDay();
        if (firstDayOfWeek === 0) firstDayOfWeek = 7; // Преобразуем воскресенье в 7

        // Добавляем пустые ячейки для дней предыдущего месяца
        for (let i = 1; i < firstDayOfWeek; i++) {
            const emptyDay = document.createElement('div');
            emptyDay.className = 'calendar-day other-month';
            grid.appendChild(emptyDay);
        }

        // Добавляем дни текущего месяца
        for (let day = 1; day <= daysInMonth; day++) {
            const dayElement = document.createElement('a');
            dayElement.className = 'calendar-day';
            dayElement.textContent = day;
            
            const currentDate = new Date(this.currentMonth.getFullYear(), this.currentMonth.getMonth(), day);
            
            // Проверяем, является ли это сегодняшним днем
            if (this.isToday(currentDate)) {
                dayElement.classList.add('today');
            }
            
            // Проверяем, есть ли расписание на этот день (будние дни)
            if (this.hasSchedule(currentDate)) {
                dayElement.classList.add('has-schedule');
            }
            
            // Добавляем ссылку на расписание
            const dateString = this.formatDate(currentDate);
            dayElement.href = `/?date=${dateString}`;
            dayElement.setAttribute('aria-label', `Расписание на ${this.formatDateReadable(currentDate)}`);
            
            grid.appendChild(dayElement);
        }

        // Добавляем пустые ячейки для дней следующего месяца
        const totalCells = 42; // 6 строк * 7 дней
        const filledCells = firstDayOfWeek - 1 + daysInMonth;
        const remainingCells = totalCells - filledCells;
        
        for (let i = 0; i < remainingCells; i++) {
            const emptyDay = document.createElement('div');
            emptyDay.className = 'calendar-day other-month';
            grid.appendChild(emptyDay);
        }
    }

    isToday(date) {
        const today = new Date();
        return date.getDate() === today.getDate() &&
               date.getMonth() === today.getMonth() &&
               date.getFullYear() === today.getFullYear();
    }

    hasSchedule(date) {
        // Расписание есть только в будние дни (понедельник-пятница)
        const dayOfWeek = date.getDay();
        return dayOfWeek >= 1 && dayOfWeek <= 5;
    }

    formatDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    formatDateReadable(date) {
        const dayNames = ['воскресенье', 'понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота'];
        const monthNames = [
            'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
            'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
        ];
        
        const day = date.getDate();
        const month = monthNames[date.getMonth()];
        const year = date.getFullYear();
        const dayOfWeek = dayNames[date.getDay()];
        
        return `${day} ${month} ${year} (${dayOfWeek})`;
    }

    updateQuickLinks() {
        const today = new Date();
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);
        
        // Обновляем ссылки с актуальными датами
        const quickLinks = document.querySelectorAll('.quick-link');
        quickLinks.forEach(link => {
            if (link.href.includes('date=tomorrow')) {
                link.href = `/?date=${this.formatDate(tomorrow)}`;
            } else if (link.href.includes('date=week')) {
                // Ссылка на текущую неделю (понедельник)
                const monday = new Date(today);
                const dayOfWeek = today.getDay();
                const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
                monday.setDate(today.getDate() - daysToMonday);
                link.href = `/?date=${this.formatDate(monday)}`;
            } else if (link.href.includes('date=next-week')) {
                // Ссылка на следующую неделю (понедельник)
                const nextMonday = new Date(today);
                const dayOfWeek = today.getDay();
                const daysToNextMonday = dayOfWeek === 0 ? 7 : 8 - dayOfWeek;
                nextMonday.setDate(today.getDate() + daysToNextMonday);
                link.href = `/?date=${this.formatDate(nextMonday)}`;
            }
        });
    }
}

// Инициализация календаря при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    new ScheduleCalendar();
});

// Добавляем функцию для создания ссылок на расписание с датами
function createScheduleLinks() {
    const links = [];
    const today = new Date();
    
    // Создаем ссылки на ближайшие 30 дней
    for (let i = 0; i < 30; i++) {
        const date = new Date(today);
        date.setDate(today.getDate() + i);
        
        if (date.getDay() >= 1 && date.getDay() <= 5) { // Только будние дни
            const dateString = formatDate(date);
            const readableDate = formatDateReadable(date);
            links.push({
                url: `https://raspisanie.space/?date=${dateString}`,
                text: `Расписание ПГУТИ на ${readableDate}`,
                date: dateString
            });
        }
    }
    
    return links;
}

function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function formatDateReadable(date) {
    const dayNames = ['воскресенье', 'понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота'];
    const monthNames = [
        'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
        'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
    ];
    
    const day = date.getDate();
    const month = monthNames[date.getMonth()];
    const year = date.getFullYear();
    const dayOfWeek = dayNames[date.getDay()];
    
    return `${day} ${month} ${year} (${dayOfWeek})`;
}

// Экспортируем функции для использования в других скриптах
window.ScheduleCalendar = ScheduleCalendar;
window.createScheduleLinks = createScheduleLinks;
