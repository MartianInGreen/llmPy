async function createSession(params, userSettings) {
    const { create } = params;
    const { apiKey } = userSettings;

    const url = 'https://api.rennersh.de/api/v1/interpreter/create'

    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + apiKey
        },
        body: JSON.stringify({ create })
    });

    return response.json();
}
