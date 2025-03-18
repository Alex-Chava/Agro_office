const buttonTexts = {
    'полка 1': { on: 'Включен', off: 'Выключен' },
    'полка 2': { on: 'Включен', off: 'Выключен' },
    'полка 3': { on: 'Включен', off: 'Выключен' },
    'полка 4': { on: 'Включен', off: 'Выключен' },
    'перемешивание': { on: 'Включен', off: 'Выключен' },
    'Канал красного света': { on: 'Включен', off: 'Выключен' },
    'Канал белого света': { on: 'Включен', off: 'Выключен' }
};

async function updateData() {
    try {
        const response = await fetch(getParametersUrl);
        const data = await response.json();

        const updateButton = (id, key) => {
            const btn = document.getElementById(id);
            if (btn) {
                const texts = buttonTexts[key] || { on: 'Включен', off: 'Выключен' };
                btn.textContent = data[key] === '1' ? texts.on : texts.off;
                btn.className = 'status-button ' + (data[key] === '1' ? 'on' : 'off');
            }
        };

        const updateText = (id, key) => {
            const elem = document.getElementById(id);
            if (elem) {
                elem.textContent = data[key];
            }
        };

        const updateStatusText = (id, key) => {
            const elem = document.getElementById(id);
            if (elem) {
                elem.textContent = data[key] === '1' ? 'вкл' : 'откл';
            }
        };

        const updateTimeText = (id, key) => {
            const elem = document.getElementById(id);
            if (elem) {
                const value = parseFloat(data[key]) || 0;
                elem.textContent = (value / 10).toFixed(0);
            }
        };

        // Новая функция для обновления графического индикатора в ячейке
        const updateBinaryIndicator = (id, key) => {
            const indicator = document.getElementById(id);
            if (indicator) {
                if (data[key] === '1') {
                    indicator.classList.remove('empty');
                    indicator.classList.add('filled');
                } else {
                    indicator.classList.remove('filled');
                    indicator.classList.add('empty');
                }
            }
        };

        updateButton('shelf1', 'полка 1');
        updateButton('shelf2', 'полка 2');
        updateButton('shelf3', 'полка 3');
        updateButton('shelf4', 'полка 4');
        updateButton('stir', 'перемешивание');
        updateButton('red-light-btn', 'Канал красного света');
        updateButton('white-light-btn', 'Канал белого света');

        updateText('red-light', 'Уровень красного света');
        updateText('white-light', 'Уровень белого света');
        updateText('UNIT_ID_PH', 'Уровень PH');
        updateText('UNIT_ID_EC', 'Уровень EC');

        // Обновляем графические индикаторы для основного бака
        updateBinaryIndicator('indicator-level-1', 'уровень БАК максимум');
        updateBinaryIndicator('indicator-level-2', 'уровень БАК центр');
        updateBinaryIndicator('indicator-level-3', 'уровень БАК минимум');

        // Обновляем графические индикаторы для баков компонентов
        updateBinaryIndicator('indicator-level-A', 'Уровень А мин');
        updateBinaryIndicator('indicator-level-B', 'Уровень В мин');
        updateBinaryIndicator('indicator-level-K', 'Уровень К мин');

        updateStatusText('statusA', 'Подача A в бак');
        updateStatusText('statusB', 'Подача В в бак');
        updateStatusText('statusK', 'Подача кислоты в бак');
        updateTimeText('timeA', 'Время подачи А в бак');
        updateTimeText('timeB', 'Время подачи В в бак');
        updateTimeText('timeK', 'Время подачи К в бак');

    } catch (error) {
        console.error("Ошибка обновления данных:", error);
    }
}

async function toggleParameter(parameterName) {
    try {
        const response = await fetch(toggleParameterUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ parameter: parameterName })
        });
        await response.json();
        updateData();
    } catch (error) {
        console.error("Ошибка переключения параметра:", error);
    }
}

async function setValue() {
    const parameterName = document.getElementById('parameter-name').value;
    const parameterValue = document.getElementById('parameter-value').value;
    try {
        const response = await fetch(setParameterValueUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ parameter: parameterName, value: parameterValue })
        });
        await response.json();
        closeModal();
        updateData();
    } catch (error) {
        console.error("Ошибка установки значения:", error);
    }
}

function openModal(parameterName) {
    document.getElementById('parameter-name').value = parameterName;
    document.getElementById('parameter-value').value = '';
    document.getElementById('valueModal').style.display = 'block';
}

function closeModal() {
    document.getElementById('valueModal').style.display = 'none';
}

window.onclick = function(event) {
    const modal = document.getElementById('valueModal');
    if (event.target === modal) {
        closeModal();
    }
};

const brightnessInput = document.getElementById('parameter-value');
if (brightnessInput) {
    brightnessInput.addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            setValue();
        }
    });
}

setInterval(updateData, 1000);
