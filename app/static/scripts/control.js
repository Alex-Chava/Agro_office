document.addEventListener('DOMContentLoaded', function() {
    const controlDateElement = document.getElementById('control-date');
    const openCollectModalButton = document.getElementById('open-collect-modal');
    const openPlantingModalButton = document.getElementById('open-planting-modal');
    const collectModal = document.getElementById('collect-modal');
    const plantingModal = document.getElementById('plantingModal');
    let selectedTrays = [];

    if (controlDateElement) {
        controlDateElement.addEventListener('change', function() {
            updateTrayStatus(this.value);
        });

        // Начальная загрузка состояния лотков
        updateTrayStatus(controlDateElement.value);
    }

    // Собираем выбранные лотки
    document.querySelectorAll('.tray input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            if (this.checked) {
                this.closest('.tray').classList.add('selected'); // Добавляем визуальную индикацию
            } else {
                this.closest('.tray').classList.remove('selected'); // Убираем визуальную индикацию
            }

            selectedTrays = Array.from(document.querySelectorAll('.tray input[type="checkbox"]:checked'))
                                 .map(cb => cb.value);
        });
    });

    // Открываем модальное окно для сбора
    if (openCollectModalButton) {
        openCollectModalButton.addEventListener('click', function() {
            updateModalContent('selected-trays-collect', 'selected-trays-input-collect');
            openModal('collect-modal');
        });
    }

    // Открываем модальное окно для посадки
    if (openPlantingModalButton) {
        openPlantingModalButton.addEventListener('click', function() {
            updateModalContent('selected-trays-planting', 'selected-trays-input-planting');
            openModal('plantingModal');
        });
    }

    // Закрытие модального окна при клике вне окна
    window.onclick = function(event) {
        if (event.target == collectModal || event.target == plantingModal) {
            closeModal(event.target.id);
        }
    };

    // Обновляем содержимое модального окна
    function updateModalContent(listId, inputId) {
        const listElement = document.getElementById(listId);
        const inputElement = document.getElementById(inputId);

        listElement.innerHTML = ''; // Очищаем список
        inputElement.value = selectedTrays.join(','); // Обновляем скрытое поле

        selectedTrays.forEach(tray => {
            const listItem = document.createElement('li');
            listItem.textContent = tray;
            listElement.appendChild(listItem);
        });
    }
});

function updateTrayStatus(date) {
    fetch(`/get_tray_status?date=${date}`)
        .then(response => response.json())
        .then(data => {
            console.log("Tray status data:", data);  // Выводит данные для проверки
            for (let trayId in data) {
                let tray = document.getElementById(`tray-${trayId}`);
                if (tray) {
                    tray.querySelector('.tray-status').textContent = data[trayId].status;
                    tray.style.backgroundImage = `url('${data[trayId].backgroundImage}')`;
                }
            }
        })
        .catch(error => console.error('Error updating tray status:', error));
}


function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
}

function submitPlanting() {
    const plantType = document.getElementById('plant_type').value;
    const growthDays = document.getElementById('growth_days').value;
    const selectedTrays = document.getElementById('selected-trays-input-planting').value.split(',');

    if (selectedTrays.length === 0 || !plantType || !growthDays) {
        alert('Заполните все поля и выберите лотки.');
        return;
    }

    fetch('/planting_action', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            trays: selectedTrays,
            plant_type: plantType,
            growth_days: growthDays
        })
    }).then(response => {
        if (response.ok) {
            closeModal('plantingModal');
            location.reload(); // Обновляем страницу после посадки
        } else {
            //alert('Ошибка при выполнении посадки.');
        }
    })
    .catch(error => console.error('Error during planting action:', error));
}

function submitCollect() {
    const selectedTrays = document.getElementById('selected-trays-input-collect').value.split(',');

    if (selectedTrays.length === 0) {
        alert('Выберите лотки для сбора.');
        return;
    }

    fetch('/collect_trays', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            trays: selectedTrays,
            plant_type: '-', // Ставим "-" для формы сбора
            growth_days: 0   // growth_days = 0 для формы сбора
        })
    }).then(response => {
        if (response.ok) {
            closeModal('collect-modal');
            location.reload(); // Обновляем страницу после сбора
        } else {
            //alert('Ошибка при выполнении сбора.');
        }
    })
    .catch(error => console.error('Error during collect action:', error));
}
