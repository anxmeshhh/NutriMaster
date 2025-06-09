function updateDashboard() {
    fetch('/dashboard_data')
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            document.getElementById('total_calories').textContent = data.total_calories;
            document.getElementById('total_protein').textContent = data.total_protein;
            const calorieChart = Chart.getChart('calorieChart');
            const proteinChart = Chart.getChart('proteinChart');
            const macroChart = Chart.getChart('macroChart');
            calorieChart.data.datasets[0].data = [data.total_calories, data.daily_calories - data.total_calories];
            proteinChart.data.datasets[0].data = [data.total_protein, data.daily_protein - data.total_protein];
            macroChart.data.datasets[0].data = [data.total_protein, data.total_carbs, data.total_fats];
            calorieChart.update();
            proteinChart.update();
            macroChart.update();
        })
        .catch(error => console.error('Error updating dashboard:', error));
}
setInterval(updateDashboard, 60000);