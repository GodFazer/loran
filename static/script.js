document.addEventListener('DOMContentLoaded', function() {
    let socket;
    const reconnectButton = document.getElementById('reconnect');

    const layout = {
        xaxis: { title: 'X', range: [-10, 110] },
        yaxis: { title: 'Y', range: [-10, 110] }
    };
        const data = [
        {
            x: [],
            y: [],
            mode: 'markers',
            type: 'scatter',
            name: 'source1',
            text: [],
            hoverinfo: 'text',
            marker: { size: 10, color: 'orange' }
        },
        {
            x: [],
            y: [],
            mode: 'markers',
            type: 'scatter',
            name: 'source2',
            text: [],
            hoverinfo: 'text',
            marker: { size: 10, color: 'blue' }
        },
        {
            x: [],
            y: [],
            mode: 'markers',
            type: 'scatter',
            name: 'source3',
            text: [],
            hoverinfo: 'text',
            marker: { size: 10, color: 'green' }
        },
        {
            x: [],
            y: [],
            mode: 'markers',
            type: 'scatter',
            name: 'Object',
            text: [],
            hoverinfo: 'text',
            marker: { size: 15, color: 'red' }
        }
    ];

    if(typeof Plotly !== 'undefined') {
        console.log("Plotly is loaded");
        Plotly.newPlot('graph', data, layout);
    } else {
        console.error("Plotly is not loaded");
    }

    function connect() {
        console.log("Attempting to connect...");
        socket = new WebSocket('ws://' + window.location.host + '/ws');

        socket.onopen = function(event) {
            console.log("Зєднання встановлено");
        };

        socket.onmessage = function(event) {
            const data = JSON.parse(event.data);
            console.log("Отримано повідомлення:", data);
            updateGraph(data);
        };
    }

    function updateGraph(data) {
        let traceIndex;

        traceIndex = data.sourceId === 'source1' ? 0 : (data.sourceId === 'source2' ? 1 : 2);

        const hoverTextSource = `ID: ${data.id.slice(-4)}<br>Source: ${data.sourceId}<br>receivedAt: ${data.receivedAt}`;

        Plotly.extendTraces('graph', {
            x: [[data.x]],
            y: [[data.y]],
            text: [[hoverTextSource]]
        }, [traceIndex]);

        if (data.Object === 'Object') {
            const hoverTextObject = `Object<br>ID: ${data.id.slice(-4)}<br>X: ${data.x_Obj}<br>Y: ${data.y_Obj}`;

            Plotly.restyle('graph', {
                x: [[data.x_Obj]],
                y: [[data.y_Obj]],
                text: [[hoverTextObject]]
            }, [3]);
        }

        Plotly.relayout('graph', {
            'xaxis.title': 'X',
            'xaxis.range': [-20, 120],
            'yaxis.title': 'Y',
            'yaxis.range': [-20, 120],
            'width': 600,
            'height': 600
        });

        Plotly.relayout('graph', {
        'xaxis.title': 'X',
        'xaxis.range': [-20, 120],
        'yaxis.title': 'Y',
        'yaxis.range': [-20, 120],
        'width': 600,
        'height': 600
        });
    }

    if (reconnectButton) {
        reconnectButton.addEventListener('click', connect);
    } else {
        console.error("Element with id 'reconnect' not found");
    }

    connect();
});

function submitConfig() {
    const objectSpeed = document.getElementById('objectSpeedInput').value;

    const config = {
        objectSpeed: parseInt(objectSpeed, 10),
    };

        fetch('/send-config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.status_code === 200) {
                document.getElementById('objectSpeed').innerText = config.objectSpeed;
                responseMessage.innerText = 'Конфігурація успішно оновлена.';
                responseMessage.style.color = 'green';
            } else {
                responseMessage.innerText = 'Помилка: ' + (data.error || 'Невідома помилка');
                responseMessage.style.color = 'red';
            }
        })
        .catch(error => {
            console.error('Помилка:', error);
            responseMessage.innerText = 'Помилка: ' + error.message;
            responseMessage.style.color = 'red';
        });
}