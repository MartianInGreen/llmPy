// ==UserScript==
// @name         Cody Interpreter Sidebar (Dark Mode)
// @namespace    http://tampermonkey.net/
// @version      0.2
// @description  Add a dark mode sidebar for managing Cody interpreter sessions
// @match        https://chatgpt.com/*
// @match        https://*.typingmind.com/*
// @grant        GM_xmlhttpRequest
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_addStyle
// ==/UserScript==

(function() {
    'use strict';

    const API_URL = 'https://api.rennersh.de';

    // Add dark mode styles
    GM_addStyle(`
        #cody-sidebar {
            background-color: #2b2b2b;
            color: #e0e0e0;
        }
        #cody-sidebar input[type="text"], #cody-sidebar textarea {
            background-color: #3b3b3b;
            color: #e0e0e0;
            border: 1px solid #555;
        }
        #cody-sidebar input[type="password"], #cody-sidebar textarea {
            background-color: #3b3b3b;
            color: #e0e0e0;
            border: 1px solid #555;
        }
        #cody-sidebar button {
            background-color: #4a4a4a;
            color: #e0e0e0;
            border: none;
            padding: 5px 10px;
            margin: 5px 0;
            cursor: pointer;
        }
        #cody-sidebar button:hover {
            background-color: #5a5a5a;
        }
        #hideSidebar, #showSidebar {
            background-color: #4a4a4a;
            color: #e0e0e0;
            border: none;
            padding: 5px 10px;
            margin-top: 5px;
            cursor: pointer;
        }
        #showSidebar {
            position: fixed;
            top: 60px;
            right: 10px;
        }
        #hideSidebar:hover, #showSidebar:hover {
            background-color: #5a5a5a;
        }
    `);

    // Create and append sidebar
    const sidebar = document.createElement('div');
    sidebar.id = 'cody-sidebar';
    sidebar.style.cssText = `
        position: fixed;
        top: 0;
        right: 0;
        width: 400px;
        height: 90%;
        margin-top: 80px;
        margin-bottom: 80px;
        padding: 20px;
        overflow-y: auto;
        overflow-x: auto;
        z-index: 1000;
        display: none; // Add this line to hide the sidebar initially
    `;
    document.body.appendChild(sidebar);

    // Add content to sidebar
    sidebar.innerHTML = `
        <h2>Cody Interpreter</h2>
        <button id="hideSidebar">Hide Sidebar</button>
        <br><br>
        <label for="adminKey">Admin Key:</label>
        <input type="password" id="adminKey">
        <button id="saveAdminKey">Save Admin Key</button>
        <span id="adminKeyIndicator"></span>
        <br><br>
        <label for="uuid">UUID:</label>
        <input type="text" id="uuid">
        <button id="createNewInterpreter">Create New</button>
        <br><br>
        <label for="dirname">Directory Name:</label>
        <input type="text" id="dirname">
        <br><br>
        <input type="file" id="file" multiple>
        <button id="uploadFiles">Upload</button>
        <br><br>
        <button id="listFiles">List Files</button>
        <button id="createDirectory">Create Directory</button>
        <button id="returnToRoot">Return to Root</button>
        <ul id="fileList"></ul>
    `;

    const hideSidebarButton = document.getElementById('hideSidebar');
    const showSidebarButton = document.createElement('button');
    showSidebarButton.textContent = 'Show Sidebar';
    showSidebarButton.style.cssText = `
        position: fixed;
        top: 60px;
        right: 10px;
        z-index: 1001;
        display: block; // Change this to 'block' to show the button initially
    `;
    document.body.appendChild(showSidebarButton);

    hideSidebarButton.onclick = function() {
        sidebar.style.display = 'none';
        showSidebarButton.style.display = 'block';
    };

    showSidebarButton.onclick = function() {
        sidebar.style.display = 'block';
        showSidebarButton.style.display = 'none';
    };

    // Implement functions
    document.getElementById('saveAdminKey').onclick = function() {
        const adminKey = document.getElementById('adminKey').value;
        GM_setValue('adminKey', adminKey);
        document.getElementById('adminKeyIndicator').textContent = 'Admin key is set';
    };

    document.getElementById('createNewInterpreter').onclick = function() {
        GM_xmlhttpRequest({
            method: 'POST',
            url: `${API_URL}/api/v1/interpreter/create`,
            headers: {
                'Authorization': 'Bearer ' + GM_getValue('adminKey'),
                'Content-Type': 'application/json'
            },
            onload: function(response) {
                const data = JSON.parse(response.responseText);
                document.getElementById('uuid').value = data.uuid;
            }
        });
    };

    document.getElementById('uploadFiles').onclick = function() {
        const files = document.getElementById('file').files;
        const uuid = document.getElementById('uuid').value;
        const dirname = document.getElementById('dirname').value;

        for (const file of files) {
            const reader = new FileReader();

            reader.onload = function(event) {
                const base64FileData = event.target.result.split(',')[1];

                GM_xmlhttpRequest({
                    method: 'POST',
                    url: `${API_URL}/api/v1/interpreter/file/upload`,
                    headers: {
                        'Authorization': 'Bearer ' + GM_getValue('adminKey'),
                        'Content-Type': 'application/json'
                    },
                    data: JSON.stringify({
                        uuid: uuid,
                        dirname: dirname,
                        filename: file.name,
                        file_data: base64FileData
                    }),
                    onload: function(response) {
                        const data = JSON.parse(response.responseText);
                        if (response.status === 200) {
                            alert(`File ${file.name} uploaded successfully.`);
                        } else {
                            alert(`Failed to upload file ${file.name}: ${data.detail}`);
                        }
                    }
                });
            };

            reader.readAsDataURL(file);
        }

        listFiles();
    };

    function listFiles() {
        GM_xmlhttpRequest({
            method: 'POST',
            url: `${API_URL}/api/v1/interpreter/file/list`,
            headers: {
                'Authorization': 'Bearer ' + GM_getValue('adminKey'),
                'Content-Type': 'application/json'
            },
            data: JSON.stringify({
                uuid: document.getElementById('uuid').value,
                dirname: document.getElementById('dirname').value
            }),
            onload: function(response) {
                const data = JSON.parse(response.responseText);
                if (response.status === 200) {
                    const fileList = document.getElementById('fileList');
                    fileList.innerHTML = '';
                    data.items.forEach(item => {
                        const listItem = document.createElement('li');
                        listItem.textContent = item.name;
                        const actionButton = document.createElement('button');
                        if (item.is_dir) {
                            actionButton.textContent = 'Enter';
                            actionButton.onclick = () => enterDirectory(item.name);
                        } else {
                            actionButton.textContent = 'Download';
                            actionButton.onclick = () => downloadFile(item.name);
                        }
                        listItem.appendChild(actionButton);
                        fileList.appendChild(listItem);
                    });
                } else {
                    alert(data.detail);
                }
            }
        });
    }

    document.getElementById('listFiles').onclick = listFiles;

    document.getElementById('createDirectory').onclick = function() {
        const dirname = prompt("Enter the name of the new directory:");
        if (dirname) {
            GM_xmlhttpRequest({
                method: 'POST',
                url: `${API_URL}/api/v1/interpreter/file/create-directory`,
                headers: {
                    'Authorization': 'Bearer ' + GM_getValue('adminKey'),
                    'Content-Type': 'application/json'
                },
                data: JSON.stringify({
                    uuid: document.getElementById('uuid').value,
                    dirname: dirname
                }),
                onload: function(response) {
                    const data = JSON.parse(response.responseText);
                    if (response.status === 200) {
                        alert('Directory created successfully.');
                        listFiles();
                    } else {
                        alert(data.detail);
                    }
                }
            });
        }
    };

    document.getElementById('returnToRoot').onclick = function() {
        document.getElementById('dirname').value = '';
        listFiles();
    };

    function enterDirectory(dirname) {
        document.getElementById('dirname').value = dirname;
        listFiles();
    }

    function downloadFile(filename) {
        const uuid = document.getElementById('uuid').value;
        GM_xmlhttpRequest({
            method: 'GET',
            url: `${API_URL}/api/v1/interpreter/file/download/${uuid}/${filename}`,
            headers: {
                'Authorization': 'Bearer ' + GM_getValue('adminKey')
            },
            responseType: 'blob',
            onload: function(response) {
                if (response.status === 200) {
                    const blob = response.response;
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.style.display = 'none';
                    a.href = url;
                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                } else {
                    const data = JSON.parse(response.responseText);
                    alert(data.detail);
                }
            }
        });
    }

    // Load admin key if previously set
    const savedAdminKey = GM_getValue('adminKey');
    if (savedAdminKey) {
        document.getElementById('adminKey').value = savedAdminKey;
        document.getElementById('adminKeyIndicator').textContent = 'Admin key is set';
    }

    // Auto-populate UUID from URL if available
    const urlParts = window.location.pathname.split('/');
    const uuid = urlParts[urlParts.length - 1];
    if (uuid && uuid.length === 32) {
        document.getElementById('uuid').value = uuid;
    }
})();
