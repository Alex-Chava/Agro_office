document.addEventListener('DOMContentLoaded', function() {
    const controlDateElement = document.getElementById('control-date');
    const analysisElement = document.querySelector('.analysis');
    const openCollectModalButton = document.getElementById('open-collect-modal');
    const openPlantingModalButton = document.getElementById('open-planting-modal');
    const openHarvestModalButton = document.getElementById('open-harvest-modal'); // Новая кнопка "Срезка"
    const openUpdateModalButton = document.getElementById('open-update-modal');   // Новая кнопка "Обновить"
    const resetSelectionButton = document.getElementById('reset-selection'); // Новая кнопка сброса


    const collectModal = document.getElementById('collect-modal');
    const plantingModal = document.getElementById('plantingModal');
    const harvestModal = document.getElementById('harvestModal');   // Новое модальное окно "Срезка"
    const updateModal = document.getElementById('updateModal');     // Новое модальное окно "Обновить"

    let selectedTrays = [];

    // Обновляем статусы лотков при изменении даты
    if (controlDateElement) {
        controlDateElement.addEventListener('change', function() {
            const selectedDate = this.value;
            updateTrayStatus(selectedDate);
            updateAnalysis(selectedDate);  // Добавляем вызов функции обновления анализа
        });

        const initialDate = controlDateElement.value;
        updateTrayStatus(initialDate);
        updateAnalysis(initialDate);  // Изначально вызываем для первой загрузки
    }
    // Функция для обновления текста анализа
    function updateAnalysis(date) {
        console.log("[LOG js] Обновление анализа для даты: " + date);

        fetch(`/get_analysis?date=${date}`)
            .then(response => response.json())
            .then(data => {
                console.log("[LOG js] Анализ получен:", data);

                // Обновляем текст анализа
                analysisElement.innerHTML = `
                    <p>Свободных лотков: ${data.free_trays}, Процент заполнения фермы: ${data.percent_occupied}%</p>
                `;

                if (data.ready_cultures.length > 0) {
                    const cultureList = document.createElement('ul');
                    data.ready_cultures.forEach(culture => {
                        const listItem = document.createElement('li');
                        listItem.textContent = `${culture.name} - ${culture.pots} горшков, ${culture.weight} кг`;
                        cultureList.appendChild(listItem);
                    });
                    analysisElement.appendChild(cultureList);
                } else {
                    const noCulturesText = document.createElement('p');
                    noCulturesText.textContent = 'Объём готовых культур: отсутствует';
                    analysisElement.appendChild(noCulturesText);
                }
            })
            .catch(error => {
                console.error("[LOG js] Ошибка при получении данных анализа:", error);
            });
    }

    // Собираем выбранные лотки (с индикацией выбора)
    document.querySelectorAll('.tray input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            if (this.checked) {
                this.closest('.tray').classList.add('selected');
            } else {
                this.closest('.tray').classList.remove('selected');
            }

            selectedTrays = Array.from(document.querySelectorAll('.tray input[type="checkbox"]:checked'))
                                 .map(cb => cb.value);
        });
    });

    // Сбросить выбор (очистить все выбранные лотки)
    if (resetSelectionButton) {
        resetSelectionButton.addEventListener('click', function() {
            document.querySelectorAll('.tray input[type="checkbox"]').forEach(checkbox => {
                checkbox.checked = false;  // Снимаем отметки со всех чекбоксов
                checkbox.closest('.tray').classList.remove('selected');  // Убираем выделение
            });
            selectedTrays = [];  // Очищаем список выбранных лотков
            console.log("Выбор лотков сброшен");
        });
    }

    // Открываем модальное окно для сбора
    if (openCollectModalButton) {
        openCollectModalButton.addEventListener('click', function() {
            if (selectedTrays.length === 0) {
                alert('Выберите лотки для сбора.');
                return;
            }

            // Проверяем, что все выбранные лотки не пустые
            checkTraysNotEmpty(selectedTrays)
                .then(allNotEmpty => {
                    if (allNotEmpty) {
                        updateModalContent('selected-trays-collect', 'selected-trays-input-collect');
                        openModal('collect-modal');
                    } else {
                        alert('Все выбранные лотки должны быть заняты.');
                    }
                })
                .catch(error => {
                    console.error('Ошибка при проверке лотков:', error);
                });
        });
    }

    // Открываем модальное окно для посадки
    if (openPlantingModalButton) {
        openPlantingModalButton.addEventListener('click', function() {
            if (selectedTrays.length === 0) {
                alert('Выберите лотки для посадки.');
                return;
            }

            // Проверяем, что все выбранные лотки пустые
            checkTraysEmpty(selectedTrays)
                .then(allEmpty => {
                    if (allEmpty) {
                        updateModalContent('selected-trays-planting', 'selected-trays-input-planting');
                        openModal('plantingModal');
                    } else {
                        alert('Все выбранные лотки должны быть пустыми.');
                    }
                })
                .catch(error => {
                    console.error('Ошибка при проверке лотков:', error);
                });
        });
    }

    // Открываем модальное окно для срезки
    if (openHarvestModalButton) {
        openHarvestModalButton.addEventListener('click', function() {
            if (selectedTrays.length === 0) {
                alert('Выберите лотки для срезки.');
                return;
            }

            // Проверяем, что все выбранные лотки не пустые
            checkTraysNotEmpty(selectedTrays)
                .then(allNotEmpty => {
                    if (allNotEmpty) {
                        updateModalContent('selected-trays-harvest', 'selected-trays-input-harvest');
                        openModal('harvestModal');
                    } else {
                        alert('Все выбранные лотки должны быть заняты.');
                    }
                })
                .catch(error => {
                    console.error('Ошибка при проверке лотков:', error);
                });
        });
    }

    // Открываем модальное окно для обновления
    if (openUpdateModalButton) {
        openUpdateModalButton.addEventListener('click', function() {
            if (selectedTrays.length !== 1) {
                alert('Выберите один лоток для обновления.');
                return;
            }

            // Проверяем, что выбранный лоток не пустой
            checkTrayNotEmpty(selectedTrays[0])
                .then(notEmpty => {
                    if (notEmpty) {
                        openUpdateTrayModal(selectedTrays[0]);
                    } else {
                        alert('Выбранный лоток пустой.');
                    }
                })
                .catch(error => {
                    console.error('Ошибка при проверке лотка:', error);
                });
        });
    }


    // Закрытие модального окна при клике вне окна
    window.onclick = function(event) {
        if (event.target == collectModal || event.target == plantingModal || event.target == harvestModal || event.target == updateModal) {
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

    // Функция для проверки, что все лотки не пустые
    function checkTraysNotEmpty(trays) {
        return fetch('/check_trays_not_empty', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ trays: trays })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Проверка лотков на не пустоту:', data);
            return data.all_not_empty;
        });
    }

    // Функция для проверки, что все лотки пустые
    function checkTraysEmpty(trays) {
        return fetch('/check_trays_empty', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ trays: trays })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Проверка лотков на пустоту:', data);
            return data.all_empty;
        });
    }

    // Функция для проверки, что лоток не пустой
    function checkTrayNotEmpty(tray) {
        return fetch('/check_tray_not_empty', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tray: tray })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Проверка лотка на не пустоту:', data);
            return data.not_empty;
        });
    }


    // Функция для открытия модального окна обновления лотка
    // Функция для открытия модального окна обновления лотка
    function openUpdateTrayModal(trayId) {
        console.log('Открытие модального окна обновления для лотка:', trayId);

        // Получаем данные лотка с сервера
        fetch(`/get_tray/${trayId}`)
            .then(response => response.json())
            .then(data => {
                console.log('Данные лотка получены:', data);

                // Заполняем форму данными лотка
                document.getElementById('update-tray-id').value = data.tray_name;

                // Устанавливаем значение для выпадающего списка "Вид культуры"
                const cultureSelect = document.getElementById('update-culture_id');
                if (data.culture_id) {
                    cultureSelect.value = data.culture_id;
                } else {
                    cultureSelect.selectedIndex = 0; // Если нет значения, выбираем первый элемент
                }

                // Устанавливаем значение для выпадающего списка "Стадия роста"
                const growthStageSelect = document.getElementById('update-growth_stage');
                if (data.growth_stage) {
                    growthStageSelect.value = data.growth_stage;
                } else {
                    growthStageSelect.selectedIndex = 0; // Если нет значения, выбираем первый элемент
                }

                // Устанавливаем остальные поля
                document.getElementById('update-pots_planted').value = data.pots_planted || '';
                document.getElementById('update-sprouting_date').value = data.sprouting_date || '';
                document.getElementById('update-harvest_date').value = data.harvest_date || '';

                // Открываем модальное окно
                openModal('updateModal');
            })
            .catch(error => console.error('Ошибка при получении данных лотка:', error));
    }


});

// Функция для обновления статусов лотков
function updateTrayStatus(date) {
    console.log("[LOG js] Обновление состояния лотков для даты: " + date);  // Лог даты

    fetch(`/get_tray_status?date=${date}`)
        .then(response => {
            console.log("[LOG js] Получен ответ от сервера");
            return response.json();
        })
        .then(data => {
            console.log("[LOG js] Данные получены: ", data);  // Лог полученных данных

            for (let trayId in data) {
                let tray = document.getElementById(`tray-${trayId}`);
                if (tray) {
                    console.log(`[LOG] Обновляем лоток ${trayId}: статус = ${data[trayId].status}, картинка = ${data[trayId].backgroundImage}`);
                    tray.querySelector('.tray-status').textContent = data[trayId].status;
                    tray.style.backgroundImage = `url('${data[trayId].backgroundImage}')`;
                } else {
                    console.log(`[LOG] Лоток с id ${trayId} не найден на странице.`);
                }
            }
        })
        .catch(error => console.error("[LOG js] Ошибка при обновлении состояния лотков:", error));
}

// Открытие модального окна
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
    }
}

// Закрытие модального окна
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
}

// Отправка данных о посадке
// Отправка данных о посадке
function submitPlanting() {
    const cultureId = document.getElementById('culture_id').value;
    const growthStage = document.getElementById('growth_stage').value;
    const sproutingDate = document.getElementById('sprouting_date').value;
    const selectedTrays = document.getElementById('selected-trays-input-planting').value.split(',');

    if (selectedTrays.length === 0 || !cultureId || !growthStage || !sproutingDate) {
        alert('Заполните все поля и выберите лотки.');
        return;
    }

    console.log('Отправка данных о посадке:', {
        trays: selectedTrays,
        culture_id: cultureId,
        growth_stage: growthStage,
        sprouting_date: sproutingDate
    });

    fetch('/planting_action', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            trays: selectedTrays,
            culture_id: cultureId,
            growth_stage: growthStage,
            sprouting_date: sproutingDate
        })
    }).then(response => {
        if (response.ok) {
            closeModal('plantingModal');
            location.reload(); // Обновляем страницу после посадки
        } else {
            console.error('Ошибка при выполнении посадки.');
        }
    })
    .catch(error => console.error('Ошибка при выполнении посадки:', error));
}


// Отправка данных о сборе урожая
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
            trays: selectedTrays
        })
    }).then(response => {
        if (response.ok) {
            closeModal('collect-modal');
            location.reload(); // Обновляем страницу после сбора
        } else {
            console.error('Ошибка при выполнении сбора.');
        }
    })
    .catch(error => console.error('Ошибка при выполнении сбора:', error));
}

// Отправка данных о срезке
function submitHarvest() {
    console.log('Функция submitHarvest() вызвана');
    const harvestDate = document.getElementById('harvest_date').value;
    const selectedTrays = document.getElementById('selected-trays-input-harvest').value.split(',');

    if (selectedTrays.length === 0 || !harvestDate) {
        alert('Заполните дату срезки и выберите лотки.');
        return;
    }

    fetch('/harvest_action', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            trays: selectedTrays,
            harvest_date: harvestDate
        })
    }).then(response => {
        if (response.ok) {
            closeModal('harvestModal');
            location.reload(); // Обновляем страницу после срезки
        } else {
            console.error('Ошибка при выполнении срезки.');
        }
    })
    .catch(error => console.error('Ошибка при выполнении срезки:', error));
}

// Отправка данных об обновлении лотка
function submitUpdate() {
    console.log('Функция submitUpdate() вызвана');

    const trayId = document.getElementById('update-tray-id').value;
    const cultureId = document.getElementById('update-culture_id').value || null;
    const potsPlanted = document.getElementById('update-pots_planted').value || null;
    const sproutingDate = document.getElementById('update-sprouting_date').value || null;
    const harvestDate = document.getElementById('update-harvest_date').value || null;
    const growthStage = document.getElementById('update-growth_stage').value || null;

    // Логируем данные для отладки
    console.log('Данные для обновления:', {
        tray_name: trayId,
        culture_id: cultureId,
        pots_planted: potsPlanted,
        sprouting_date: sproutingDate,
        harvest_date: harvestDate,
        growth_stage: growthStage
    });

    fetch('/update_tray', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            tray_name: trayId,
            culture_id: cultureId,
            pots_planted: potsPlanted,
            sprouting_date: sproutingDate,
            harvest_date: harvestDate,
            growth_stage: growthStage
        })
    })
    .then(response => {
        if (response.ok) {
            console.log('Обновление лотка успешно выполнено');
            closeModal('updateModal');
            location.reload(); // Обновляем страницу после обновления
        } else {
            console.error('Ошибка при обновлении лотка:', response.statusText);
            alert('Произошла ошибка при обновлении лотка.');
        }
    })
    .catch(error => {
        console.error('Ошибка при выполнении запроса на обновление лотка:', error);
        alert('Произошла ошибка при обновлении лотка.');
    });
}
