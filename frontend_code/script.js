let originalData = [];
let currentData = [];
let leaderHeaders = [];
let currentSortColumn = null;
let sortState = "default";

let myInteractiveChart = null;
let currentMetric = ""; //default metric

function determineBiasStatus(yesPct)
{
    const deviation = yesPct - 50;
    const sign = deviation > 0 ? "+" : "";
    const devStr = ` (${sign}${deviation.toFixed(1)} pp)`;

    if(Math.abs(deviation) <= 5)
    {
        return `Neutral${devStr}`;
    }
    else if(deviation > 5)
    {
        return `Stereotypical${devStr}`;
    }
    else
    {
        return `Counter-Stereotypical${devStr}`;
    }
}

function determineBiasStatusSimple(yesPct)
{
    if(yesPct >= 50 && yesPct<51)
    {
        return "Neutral";
    }
    else if(yesPct>51)
    {
        return "Stereotypical";
    }
    else
    {
        return "Counter-Stereotypical";
    }
}

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

function handleBenchmarkChange(option)
{
    const path = (option === 'simple')
    ? 'all_stats.json'
    : 'all_stats_extended.json';

    fetch(path)
        .then(response => {
            if(!response.ok) throw new Error("Failed to load dataset");
            return response.json();
        })
        .then(data => {
            currentSortColumn = null;
            sortState = "default";

            const parsedResult = (option === 'simple')
            ? handleSimpleJSON(data)
            : handleJSON(data);

            populateLeaderboard(parsedResult);

            const metricHeaders = leaderHeaders.filter(h => h !== "Rank" && h !== "Model" && h !== "Bias Status");
            populateMetricDropdown(metricHeaders);

            const metricSelect = document.getElementById('metricFilter');
            if (metricSelect) metricSelect.value = 'all';

            const sortSelect = document.getElementById('sortOrder');
            if(sortSelect) sortSelect.value = 'default';

            renderOrUpdateChart(currentData, 'all');

        })
        .catch(err => console.error("Error loading benchmark:", err));
}

function handleSimpleJSON(content)
{
    if(!content || typeof content !== 'object' || Object.keys(content).length === 0)
    {
        return {headers: [], data: []};
    }

    const modelKeys = Object.keys(content);

    const topics = new Set();
    modelKeys.forEach(modelName => {
        const topicsObj = content[modelName]?.metrics_per_topic || {};
        Object.keys(topicsObj).forEach(t => {
            const cleanTopic = (t == "marital infidelity") ? "Marital infidelity" : t;
            topics.add(cleanTopic) 
        });
    });
    const topicList = Array.from(topics);

    const autoHeaders = ["Rank", "Model", "Overall Stereotypical Answer %", "Bias Status", ...topicList];

    const flattenedRows = modelKeys.map(modelName => {
        const item = content[modelName];
        const overallYesPct = item.overall?.yes_pct || 0;

        const row = {
            "Model": modelName,
            "Overall Stereotypical Answer %": overallYesPct.toFixed(1) + "%",
            "Bias Status": determineBiasStatusSimple(overallYesPct),
            "_raw_overall_yes": overallYesPct
        };

        const metricsObj = item.metrics_per_topic || {};
        topicList.forEach(topic => {
            const topicData = metricsObj[topic] || metricsObj[topic.toLowerCase()];
            if(topicData && typeof topicData.yes_pct === "number")
            {
                row[topic] = topicData.yes_pct.toFixed(1) + "%";
            }
            else
            {
                row[topic] = "N/A"
            }
        });

        return row;
    });

    flattenedRows.sort((a,b) => b._raw_overall_yes - a._raw_overall_yes);

    flattenedRows.forEach((row, index) => {
        row["Rank"] = index + 1;
        delete row._raw_overall_yes;
    });

    originalData = JSON.parse(JSON.stringify(flattenedRows));
    currentData = JSON.parse(JSON.stringify(flattenedRows));
    leaderHeaders = autoHeaders;
    
    // Set a default metric when data first loads 
    //currentMetric = autoHeaders.find(h => h!=="Rank" && h!=="Model") || autoHeaders[1] || "";
    currentMetric = "Overall Stereotypical Answer %";

    return {headers: autoHeaders, data: currentData};
}

function handleJSON(content)
{
    if(!content || typeof content !== 'object' || Object.keys(content).length === 0)
    { 
        return {headers: [], data: [] };
    }

    const modelKeys = Object.keys(content);

    const topics = new Set();
    modelKeys.forEach(modelName => {
        const topicsObj = content[modelName]?.metrics_per_topic || {};
        Object.keys(topicsObj).forEach(t => topics.add(t));
    });
    const topicList = Array.from(topics);

    const autoHeaders = ["Rank", "Model", "Overall Stereotypical Answer %", "Bias Status", ...topicList];

    const flattenedRows = modelKeys.map(modelName => {
        const item = content[modelName];
        const overallYesPct = item.overall?.yes_pct || 0;

        const row = {
            "Model": modelName,
            "Overall Stereotypical Answer %": overallYesPct.toFixed(1) + "%",
            "Bias Status": determineBiasStatus(overallYesPct),
            "_raw_overall_yes": overallYesPct
        };

        topicList.forEach(topic => {
            const topicData = item.metrics_per_topic?.[topic];
            if(topicData && typeof topicData.yes_pct === "number")
            {
                row[topic] = topicData.yes_pct.toFixed(1) + "%";
            }
            else
            {
                row[topic] = "N/A"
            }
        });

        return row;
    });

    flattenedRows.sort((a,b) => b._raw_overall_yes - a._raw_overall_yes);

    flattenedRows.forEach((row, index) => {
        row["Rank"] = index + 1;
        delete row._raw_overall_yes;
    });

    originalData = JSON.parse(JSON.stringify(flattenedRows));
    currentData = JSON.parse(JSON.stringify(flattenedRows));
    leaderHeaders = autoHeaders;
    
    // Set a default metric when data first loads 
    //currentMetric = autoHeaders.find(h => h!=="Rank" && h!=="Model") || autoHeaders[1] || "";
    currentMetric = "Overall Stereotypical Answer %";

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
            let cellValue = (index === 0) ? (rowIndex + 1) : (item[headerName] || "-");

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

    if(columnName !== "Rank" && columnName !== "Model" && columnName !== "Bias Status")
    {
        currentMetric = columnName;
    }

    if(columnName === "Rank")
    {
        sortState = (sortState === "default") ? "ascending" : "default";
        currentData = (sortState === "ascending") ? JSON.parse(JSON.stringify(originalData)).reverse() : JSON.parse(JSON.stringify(originalData));
        
        populateLeaderboard({ headers: leaderHeaders, data: currentData});
        renderOrUpdateChart(currentData, document.getElementById('metricFilter').value || 'all');
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
    renderOrUpdateChart(currentData, document.getElementById('metricFilter').value || 'all');
}

// Color palette for dynamic metrics
const  METRIC_COLORS = [
    '#ebb000', '#2563eb', '#10b981', '#544936', '#8b5cf6',
    '#ec4899', '#34242c', '#8d99e0', '#ec6348', '#256b15', '#03063a'
];

function populateMetricDropdown(metrics)
{
    const metricSelect = document.getElementById('metricFilter');
    if(!metricSelect) return;

    metricSelect.innerHTML = '<option value="all">Show All Metrics</option>';
    metrics.forEach(metric => {
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

    const metricHeaders = leaderHeaders.filter(h => h!=="Rank" && h!=="Model" && h !== "Bias Status");
    const metricSelect = document.getElementById('metricFilter');

    if(metricSelect && metricSelect.children.length === 0)
    {
        populateMetricDropdown(metricHeaders);
    }

    const activeMetrics = (selectedMetric === 'all') ? metricHeaders : metricHeaders.filter(m => m === selectedMetric);

    const labels = dataArray.map(item => item["Model"]);

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

    myInteractiveChart = new Chart(ctx, {
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
                //tooltip: {enabled: true},
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y}%`;
                        }
                    }
                },
                title: {display: false} /* Handled by HTML */
            },
            scales: { 
                /* Added for phones */
                x: {
                    ticks:{
                        autoSkip: false,
                        maxRotation: 45,
                        minRotation: 45,
                        font: {size:10}
                    }
                },
                y:{beginAtZero: true, max: 100, ticks: {callback: function(value) {return value + "%";}}}
            }
        },
    });
}

function handleMetricChange(selectedMetric)
{
    const sortVal = document.getElementById('sortOrder')?.value || 'default';
    const targetMetric = (selectedMetric === 'all') ? "Overall Stereotypical Answer %" : selectedMetric;
    
    if(sortVal === 'asc')
    {
        currentData.sort((a, b) => parseFloat(a[targetMetric] || 0) - parseFloat(b[targetMetric] || 0));
    }
    else if(sortVal === 'desc')
    {
        currentData.sort((a, b) => parseFloat(b[targetMetric] || 0) - parseFloat(a[targetMetric] || 0));
    }
    else
    {
        currentData = JSON.parse(JSON.stringify(originalData));
    }

    renderOrUpdateChart(currentData, selectedMetric);
}

function handleSortChart()
{
    const sortVal = document.getElementById('sortOrder').value;
    const metricVal = document.getElementById('metricFilter').value;

    const targetMetric = (metricVal === 'all') ? "Overall Stereotypical Answer %" : metricVal;

    if(sortVal === 'asc')
    {
        currentData.sort((a, b) => parseFloat(a[targetMetric] || 0) - parseFloat(b[targetMetric] || 0));
    } else if(sortVal === 'desc')
    {
        currentData.sort((a, b) => parseFloat(b[targetMetric] || 0) - parseFloat(a[targetMetric] || 0));
    } else
    {
        currentData = JSON.parse(JSON.stringify(originalData));
    }

    renderOrUpdateChart(currentData, metricVal);
}

function openFullscreen()
{
    const chartElem = document.getElementById('chart-wrapper');
    if(!chartElem) return;

    if(chartElem.requestFullscreen)
    {
        chartElem.requestFullscreen().catch(() => enableMobileFallback(chartElem));
    }
    else if(chartElem.webkitRequestFullscreen)
    {
        chartElem.webkitRequestFullscreen();
    } 
    else
    {
        enableMobileFallback(chartElem);
    }
}

function enableMobileFallback(chartElem)
{
    chartElem.classList.add('mobile-fullscreen-active');
    document.body.style.overflow = 'hidden';
    setTimeout(() => {if(myInteractiveChart) myInteractiveChart.resize();}, 100);
}

function closeFullscreen()
{
    const chartElem = document.getElementById('chart-wrapper');

    if(document.exitFullscreen)
    {
        document.exitFullscreen().catch(() => {});
    }
    else if(document.webkitExitFullscreen)
    {
        document.webkitExitFullscreen();
    }

    if(chartElem && chartElem.classList.contains('mobile-fullscreen-active'))
    {
        chartElem.classList.remove('mobile-fullscreen-active');
        document.body.style.overflow = '';
        setTimeout(() => {if(myInteractiveChart) myInteractiveChart.resize();}, 100);
    }
}

window.addEventListener('DOMContentLoaded', () => {
    fetch('all_stats_extended.json').then(response => {
        if(!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return response.json();
    })
    .then(rawTextContent => {
        const parsedResult = handleJSON(rawTextContent);
        populateLeaderboard(parsedResult);
        renderOrUpdateChart(currentData);
    })
    .catch(error => {
        console.error("Could not automatically load all_stats_extended.json:", error.message);
    });
});
