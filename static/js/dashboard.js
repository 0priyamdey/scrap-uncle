// so basically i wanted to add some grah's in the homepage so that user can see and asses his/her analytics in an wasy way.
// so I asked gemini to help on that part, and it told me there is .js library called chart.js, and it can help me make charts on the data, s I went to the site of chart.js
// i.e. chartjs.org and read there few documentations selected this two basic charts and used them in the project, obiviouly took some help from the google to make it happen but,
// the code is wriiten and modified by myself only.

document.addEventListener("DOMContentLoaded", () => {

    const analytics = document.getElementById("data-analytics");

    const data = JSON.parse(analytics.dataset.analytics);
    console.log(data);

    const categories = data.map(item => item.category.toUpperCase());
    const weights = data.map(item => item.cat_weight);
    const amounts = data.map(item => item.cat_total);

    console.log(categories);
    console.log(weights);
    console.log(amounts);

    const palette = ['#198754', '#0d6efd', '#ffc107', '#fd7e14', '#20c997', '#6f42c1'];

    const weightChart = document.getElementById("weight-chart");
    if (weightChart) {
        new Chart(weightChart, {
            type: 'doughnut',
            data: {
                labels: categories,
                datasets: [{
                    data: weights,
                    backgroundColor: palette,
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: { boxWidth: 12, padding: 20 }
                    }
                },
                cutout: '50%'
            }
        })
    };

    const moneyChart = document.getElementById("money-chart")
    if (moneyChart) {
        new Chart(moneyChart, {
            type: 'bar',
            data: {
                labels: categories,
                datasets: [{
                    label: 'Earnings',
                    data: amounts,
                    backgroundColor: palette,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: { beginAtZero: true, grid: { color: "#f0f0f0" } },
                    x: { grid: { display: false } }
                }
            }
        })
    };


});
