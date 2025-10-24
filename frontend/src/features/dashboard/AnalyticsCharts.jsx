import React from 'react';
import { ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import './AnalyticsCharts.css';

const COLORS = ['#C0A35E', '#A0A0A0', '#333333', '#0B0B0B']; // Colores para los gráficos

const AnalyticsCharts = ({ bosses, weaponStats }) => {
  // Función de ayuda para procesar los datos de jefes por tier
  const processBossTierData = (bossesList) => {
    const bossTierCounts = {};
    // Asegurarse de que bossesList sea un array antes de iterar
    if (Array.isArray(bossesList)) {
      bossesList.forEach(boss => {
        const tier = boss.boss_tier || 'Unknown'; // Usar 'Unknown' si boss_tier no está definido
        bossTierCounts[tier] = (bossTierCounts[tier] || 0) + 1;
      });
    }
    
    // Transformar el objeto contador en el formato que recharts necesita
    return Object.keys(bossTierCounts).map(tier => ({
      name: tier,
      value: bossTierCounts[tier],
    }));
  };

  // Corregido: bosses prop ya es el array de items
  const pieChartData = Array.isArray(bosses) ? processBossTierData(bosses) : [];

  // Preparar datos para el BarChart de Estadísticas de Armas
  const barChartData = [];
  if (weaponStats && weaponStats.top_damage) {
    weaponStats.top_damage.forEach(weapon => {
      barChartData.push({
        name: weapon.name,
        damage: weapon.damage,
      });
    });
  }

  return (
    <div className="analytics-charts-container">
      <Card className="chart-card">
        <CardHeader>
          <CardTitle>Distribución de Jefes por Tier</CardTitle>
        </CardHeader>
        <CardContent>
          {pieChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieChartData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {pieChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p>No hay datos de tiers de jefes disponibles.</p>
          )}
        </CardContent>
      </Card>

      <Card className="chart-card">
        <CardHeader>
          <CardTitle>Top 5 Armas por Daño Físico</CardTitle>
        </CardHeader>
        <CardContent>
          {barChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={barChartData}
                margin={{
                  top: 5, right: 30, left: 20, bottom: 5,
                }}
              >
                <XAxis dataKey="name" stroke="var(--color-text-secondary)" />
                <YAxis stroke="var(--color-text-secondary)" />
                <Tooltip />
                <Legend />
                <Bar dataKey="damage" fill="var(--color-accent-gold)" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p>No hay datos de estadísticas de armas disponibles.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default AnalyticsCharts;