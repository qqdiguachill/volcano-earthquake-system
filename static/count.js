document.addEventListener("DOMContentLoaded", function () {
    // 地震統計圖
    const ctx1 = document.getElementById('earthquakeChart').getContext('2d');
    new Chart(ctx1, {
        type: 'bar',
        data: {
            labels: window.chartData.labels,
            datasets: [{
                label: '地震次數',
                data: window.chartData.data,
                backgroundColor: 'rgba(75, 192, 192, 0.6)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: { responsive: true }
    });

    // 火山事件每日統計圖
    const ctx2 = document.getElementById('volcanoChart').getContext('2d');
    new Chart(ctx2, {
        data: {
            labels: window.chartData.volcano_labels,
            datasets: [
                {
                    type: 'bar',
                    label: '每日事件數',
                    data: window.chartData.volcano_data,
                    backgroundColor: 'rgba(255, 99, 132, 0.6)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1
                },
                {
                    type: 'line',
                    label: '事件趨勢',
                    data: window.chartData.volcano_data,
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    fill: false,
                    tension: 0.3
                }
            ]
        },
        options: { responsive: true }
    });

    // 平滑滾動效果
    //const eqChart = document.getElementById('earthquakeChart');
    //const volcanoChart = document.getElementById('volcanoChart');

    // 找到標題元素
    const eqTitle = document.querySelector('h1:nth-of-type(1)');
    const volcanoTitle = document.querySelector('h1:nth-of-type(2)');

    // 在地震圖表區塊滾輪往下時 → 捲到火山標題
    eqChart.addEventListener('wheel', function (event) {
        if (event.deltaY > 0) {
            event.preventDefault();
            volcanoTitle.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });

    // 在火山圖表區塊滾輪往上時 → 捲回地震標題
    volcanoChart.addEventListener('wheel', function (event) {
        if (event.deltaY < 0) {
            event.preventDefault();
            eqTitle.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
});
