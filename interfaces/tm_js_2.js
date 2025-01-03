async function pythonInterpreterListFiles(params, userSettings) {
    const { uuid, dirname } = params;
    const { apiKey } = userSettings;

    const url = 'https://api.rennersh.de/api/v1/interpreter/file/list'

    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + apiKey
        },
        body: JSON.stringify({ uuid, dirname })
    });

    return response.json();
}