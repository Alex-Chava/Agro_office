function openAddScenarioModal(type) {
    document.getElementById('scenario-type').value = type;
    const parameterSelect = document.getElementById('scenario-parameter');
    const valueSelect = document.getElementById('scenario-value');
    const valueNumber = document.getElementById('scenario-value-number');
    parameterSelect.innerHTML = ''; // Очищаем список параметров
    valueSelect.style.display = 'block';
    valueNumber.style.display = 'none';

    const polivParameters = [
        'полка 1', 'полка 2', 'полка 3', 'полка 4', 'перемешивание'
    ];

    const svetParameters = [
        'Канал красного света', 'Канал белого света'
    ];

    const levelParameters = [
        'Уровень красного света', 'Уровень белого света'
    ];

    const parameters = type === 'Полив' ? polivParameters : svetParameters.concat(levelParameters);

    parameters.forEach(param => {
        const option = document.createElement('option');
        option.value = param;
        option.text = param;
        parameterSelect.add(option);
    });

    parameterSelect.addEventListener('change', () => {
        if (levelParameters.includes(parameterSelect.value)) {
            valueSelect.style.display = 'none';
            valueNumber.style.display = 'block';
        } else {
            valueSelect.style.display = 'block';
            valueNumber.style.display = 'none';
        }
    });

    document.getElementById('addScenarioModal').style.display = 'block';
}

function closeModal() {
    document.getElementById('addScenarioModal').style.display = 'none';
}

function addScenario() {
    const form = document.getElementById('addScenarioForm');
    const formData = new FormData(form);
    const data = {};
    formData.forEach((value, key) => {
        data[key] = value;
    });

    // Проверяем, какое значение использовать
    if (document.getElementById('scenario-value-number').style.display === 'block') {
        data['value'] = document.getElementById('scenario-value-number').value;
    }

    console.log('Form data to send:', data);  // Вывод данных формы в консоль

    fetch('/add_scenario', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        console.log('Server response:', result);  // Вывод ответа сервера в консоль
        if (result.success) {
            closeModal();
            location.reload(); // Обновляем страницу для отображения новых данных
        } else {
            alert('Error adding scenario: ' + result.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);  // Вывод ошибки в консоль
    });
}


function deleteScenario(id, type) {
    fetch('/delete_scenario', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ id: id })
    })
    .then(response => response.json())
    .then(result => {
        location.reload(); // Обновляем страницу для отображения новых данных
    })
    .catch(error => {
        console.error('Error:', error);  // Вывод ошибки в консоль
    });
}
