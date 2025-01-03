async function pythonInterpreter(params, userSettings) {
    const { uuid, code } = params;
    const { apiKey } = userSettings;

    const url = 'https://api.rennersh.de/api/v1/interpreter/python'

    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + apiKey
        },
        body: JSON.stringify({ uuid, code })
    });

    return response.json();
}

