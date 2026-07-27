let originalData = [];
let currentData = [];
let leaderHeaders = [];
let currentSortColumn = null;
let sortState = "default";

function handleTSV(content)
{
    const rows = content.split(/\r?\n/).map(r => r.trim()).filter(r => r);
    if(rows.length === 0) return { headers: [], data: [] };

    let maxColumns = 0;
    rows.forEach(row => {
        const columnsCount = row.split('\t').length;
        if(columnsCount > maxColumns) maxColumns = columnsCount;
    });

    const autoHeaders = [];
    autoHeaders.push(`Rank`);
    autoHeaders.push(`Model`);
    for(let c = 1; c <= maxColumns-2; c++)
    {
        autoHeaders.push(`Metric_${c}`);
    }

    const parsedData = [];
    for(let i = 0; i < rows.length; i++)
    {
        const values = rows[i].split('\t');
        const rowObject = {};
        for(let j = 0; j < autoHeaders.length; j++)
        {
            rowObject[autoHeaders[j]] = values[j] ? values[j].trim() : "";
        }

        parsedData.push(rowObject);
    }

    return { headers: autoHeaders, data: parsedData };
}

function handleJSON(content)
{
    if(content.length === 0)
    { 
        return {headers: [], data: [] };
    }

    const autoHeaders = Object.keys(content[0]);

    originalData = JSON.parse(JSON.stringify(content));
    currentData = JSON.parse(JSON.stringify(content));
    leaderHeaders = autoHeaders;

    return {headers: autoHeaders, data: currentData};
}

function populateLeaderboard(parsedResult)
{
    const {headers, data} = parsedResult;
    const tableHeader = document.getElementById('leaderboard-header');
    const tableBody = document.getElementById('leaderboard-body');

    if(!tableHeader || !tableBody) return;

    let headerHTML = "";
    headers.forEach((headerName, index) => {
        let arrow = "↑↓";
        let activeClass = "";

        if(currentSortColumn === headerName)
        {
            if(sortState === "descending")
            {
                arrow = " ↓";
                activeClass = "active-sort";
            } else if(sortState === "ascending")
            {
                arrow = " ↑";
                activeClass = "active-sort";
            }
        }

        if(index === 0)
        {
            headerHTML += `<th class="rank-col ${activeClass}" onclick="toggleSort('${headerName}')">${headerName}<span class="sort-icon">${arrow}</span></th>`;
        } else
        {
            headerHTML += `<th class="${activeClass}" onclick="toggleSort('${headerName}')">${headerName}<span class="sort-icon">${arrow}</span></th>`;
        }
    });
    tableHeader.innerHTML = headerHTML;

    tableBody.innerHTML = "";
    data.forEach((item, rowIndex) => {
        let rowHTML = "<tr>";

        headers.forEach((headerName, index) => {
            let cellValue = (index === 0) ? (rowIndex + 1) : item[headerName];

            if(index === 0)
            {
                rowHTML += `<td class="rank-col">${cellValue}</td>`;
            } else
            {
                rowHTML += `<td>${cellValue}</td>`
            }
        });

        rowHTML += "</tr>";
        tableBody.insertAdjacentHTML('beforeend', rowHTML);
    });
}

function toggleSort(columnName)
{
    if(currentSortColumn !== columnName)
    {
        currentSortColumn = columnName;
        sortState = "default";
    }

    if(columnName === "Rank")
    {
        sortState = (sortState === "default") ? "ascending" : "default";
        currentData = (sortState === "ascending") ? JSON.parse(JSON.stringify(originalData)).reverse() : JSON.parse(JSON.stringify(originalData));
        
        populateLeaderboard({ headers: leaderHeaders, data: currentData});
        return;
    }

    if(sortState === "default")
    {
        sortState = "descending";
    } else if(sortState === "descending")
    {
        sortState = "ascending";
    } else
    {
        sortState = "default";
    }

    if(sortState === "default")
    {
        currentData = JSON.parse(JSON.stringify(originalData));
    } else
    {
        currentData.sort((rowA, rowB) => {
            const valA = rowA[columnName] || "";
            const valB = rowB[columnName] || "";
            const numA = parseFloat(valA);
            const numB = parseFloat(valB);
            const isNumeric = !isNaN(numA) && !isNaN(numB);

            if(sortState === "descending")
            {
                return isNumeric ? numB - numA : valB.localeCompare(valA, undefined, { numeric: true});
            } else
            {
                return isNumeric ? numA - numB : valA.localeCompare(valB, undefined, { numeric: true});
            }
        });
    }

    populateLeaderboard({ headers: leaderHeaders, data: currentData});
}

window.addEventListener('DOMContentLoaded', () => {
    fetch('data.json').then(response => {
        if(!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return response.json();
    })
    .then(rawTextContent => {
        const parsedResult = handleJSON(rawTextContent);
        populateLeaderboard(parsedResult);
    })
    .catch(error => {
        console.error("Could not automatically load data.json:", error.message);
    });
});
