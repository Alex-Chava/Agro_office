// Открытие модального окна для добавления/обновления культуры
function openCultureModal(cultureId) {
    const modal = document.getElementById('culture-modal');
    const title = document.getElementById('culture-modal-title');

    if (cultureId) {
        // Обновление записи
        title.textContent = 'Обновить культуру';
        // Загрузка данных через AJAX и заполнение формы
        fetch(`/get_culture/${cultureId}`)
            .then(response => response.json())
            .then(data => {
                document.getElementById('culture_id').value = data.culture_id;
                document.getElementById('name').value = data.name;

                // Сроки пребывания в предварительных зонах
                document.getElementById('sprouting_in_chamber_days').value = data.sprouting_in_chamber_days;
                document.getElementById('sprouting_on_shelf_days').value = data.sprouting_on_shelf_days;
                document.getElementById('seedling_days').value = data.seedling_days;

                // Вместимость на полке
                document.getElementById('pots_at_sprouting').value = data.pots_at_sprouting;
                document.getElementById('pots_at_seedling').value = data.pots_at_seedling;
                document.getElementById('pots_at_main_stage').value = data.pots_at_main_stage;

                // Первичное созревание от посадки зерна
                document.getElementById('min_days_from_planting').value = data.min_days_from_planting;
                document.getElementById('min_weight_from_planting').value = data.min_weight_from_planting;
                document.getElementById('max_days_from_planting').value = data.max_days_from_planting;
                document.getElementById('max_weight_from_planting').value = data.max_weight_from_planting;

                // Повторное созревание после срезки
                document.getElementById('min_days_from_cutting').value = data.min_days_from_cutting;
                document.getElementById('min_weight_from_cutting').value = data.min_weight_from_cutting;
                document.getElementById('max_days_from_cutting').value = data.max_days_from_cutting;
                document.getElementById('max_weight_from_cutting').value = data.max_weight_from_cutting;
            });
    } else {
        // Добавление новой записи
        title.textContent = 'Добавить культуру';
        document.getElementById('cultureForm').reset();
        // Сбросить скрытое поле culture_id
        document.getElementById('culture_id').value = '';
    }

    modal.style.display = 'block';
}

// Закрытие модального окна
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Удаление культуры
function deleteCulture(cultureId) {
    if (confirm(`Вы уверены, что хотите удалить культуру с ID ${cultureId}?`)) {
        fetch(`/delete_culture/${cultureId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        }).then(response => {
            if (response.ok) {
                location.reload(); // Обновляем страницу после удаления
            } else {
                alert('Ошибка при удалении культуры.');
            }
        });
    }
}

// Инициализация таблицы с DataTables
$(document).ready(function() {
    $('#culturesTable').DataTable({
        scrollX: true,                 // Включает горизонтальную прокрутку
        autoWidth: false,              // Отключает автоматическую ширину для колонок
        language: {
            url: "//cdn.datatables.net/plug-ins/1.11.5/i18n/Russian.json"
        },
        columnDefs: [
            { width: "15px", targets: 0 },  // Ширина для первой колонки "Название"
            { width: "10px", targets: 1 },  // Ширина для "Проращивание в камере (дней)"
            { width: "10px", targets: 2 },  // Ширина для "Проращивание на полке (дней)"
            { width: "10px", targets: 3 },  // И так далее
            { width: "10px", targets: 4 }  // Настройте ширину остальных колонок аналогично
            // Добавьте настройки ширины для всех колонок, которые необходимо ограничить
        ],
        paging: true,                  // Включает пагинацию
        searching: true,               // Включает поиск
        ordering: true,                // Включает сортировку
        fixedColumns: true             // Фиксирует ширину колонок при изменении
    });
});
