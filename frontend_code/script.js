let originalData = [];
let currentData = [];
let leaderHeaders = [];
let currentSortColumn = null;
let sortState = "default";

let myInteractiveChart = null;
let currentMetric = ""; //default metric

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
    
    // Set a default metric when data first loads 
    currentMetric = autoHeaders.find(h => h!=="Rank" && h!=="Model") || autoHeaders[1] || "";

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

    if(columnName !== "Rank" && columnName !== "Model")
    {
        currentMetric = columnName;
    }

    if(columnName === "Rank")
    {
        sortState = (sortState === "default") ? "ascending" : "default";
        currentData = (sortState === "ascending") ? JSON.parse(JSON.stringify(originalData)).reverse() : JSON.parse(JSON.stringify(originalData));
        
        populateLeaderboard({ headers: leaderHeaders, data: currentData});
        renderOrUpdateChart(currentData);
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
    renderOrUpdateChart(currentData);
}

// Color palette for dynamic metrics
const  METRIC_COLORS = [
    '#ebb000', '#2563eb', '#10b981', '#544936', '#8b5cf6',
    '#ec4899', '#34242c', '#8d99e0', '#ec6348', '#256b15'
];

function populateMetricDropdown(metric)
{
    const metricSelect = document.getElementById('metricFilter');
    if(!metricSelect) return;

    metricSelect.innerHTML = '<option value="all">Show All Metrics</option>';
    metricSelect.forEach(metric => {
        const option = document.createElement('option');
        option.value = metric;
        option.textContent = metric;
        metricSelect.appendChild(option);
    });
}

function renderOrUpdateChart(dataArray, selectedMetric = 'all')
{
    const canvas = document.getElementById('mainChart');
    if(!canvas || !dataArray || dataArray.length === 0) return;
    const ctx = canvas.getContext('2d');

    const metricHeaders = leaderHeaders.filter(h => h!=="Rank" && h!=="Model");
    const metricSelect = document.getElementById('metricFilter');

    if(metricSelect && metricSelect.children.length === 0)
    {
        populateMetricDropdown(metricHeaders);
    }

    const activeMetrics = (selectedMetric === 'all') ? metricHeaders : metricHeaders.filter(m => m === selectedMetric);

    const labels = dataArray.map(item => item["Model"] || item[Object.keys(item)[0]]);

    const datasets = activeMetrics.map((metric) => {
        const originalIndex = metricHeaders.indexOf(metric);
        const color = METRIC_COLORS[originalIndex % METRIC_COLORS.length];

        return {
            label: metric,
            data: dataArray.map(item => parseFloat(item[metric]) || 0),
            backgroundColor: color,
            borderColor: '#1f2937',
            borderWidth: 1
        };
    });

    if(myInteractiveChart)
    {
        myInteractiveChart.destroy();
    }

    myInteractiveChart = new CharacterData(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {display: true, position: 'top'},
                tooltip: {enabled: true},
                title: {display: false} /* Handled by HTML */
            },
            scales: { 
                y:{beginAtZero: true, max: 1.0}
            }
        },
    });
}

function handleMetricChange(selectedMetric)
{
    renderOrUpdateChart(currentData, selectedMetric);
}

function handleSortChart()
{
    const sortVal = document.getElementById('sortOrder').value;
    const metricVal = document.getElementById('metricFilter').value;

    if(sortVal === 'asc')
    {
        currentData.sort((a, b) => parseFloat(a[metricVal] || 0) - parseFloat(b[metricVal] || 0));
    } else if(sortVal === 'desc')
    {
        currentData.sort((a, b) => parseFloat(b[metricVal] || 0) - parseFloat(a[metricVal] || 0));
    } else
    {
        currentData = JSON.parse(JSON.stringify(originalData));
    }

    renderOrUpdateChart(currentData, metricVal);
}

function openFullscreen()
{
    const chartElem = document.getElementById('chart-wrapper');
    if(chartElem && chartElem.requestFullscreen)
    {
        chartElem.requestFullscreen();
    }
}

function closeFullscreen()
{
    if(document.exitFullscreen)
    {
        document.exitFullscreen();
    }
}

window.addEventListener('DOMContentLoaded', () => {
    fetch('data.json').then(response => {
        if(!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return response.json();
    })
    .then(rawTextContent => {
        const parsedResult = handleJSON(rawTextContent);
        populateLeaderboard(parsedResult);
        renderOrUpdateChart(currentData);
    })
    .catch(error => {
        console.error("Could not automatically load data.json:", error.message);
    });
});
