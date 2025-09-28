import React from 'react';
import { Card } from 'antd';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { Row } from '../../types';

interface WindSpeedChartProps {
  data: Row[];
}

const WindSpeedChart: React.FC<WindSpeedChartProps> = ({ data }) => {
  // Filtrer les données de vitesse du vent
  const windData = data.filter(row => row.metric_name === 'avg_windspeed');

  // Transformer les données pour Recharts
  const chartData = windData.reduce((acc: any[], row) => {
    const existingEntry = acc.find(entry => entry.metric_date === row.metric_date);
    if (existingEntry) {
      existingEntry[row.location] = row.metric_value;
    } else {
      acc.push({
        metric_date: row.metric_date,
        [row.location]: row.metric_value,
      });
    }
    return acc;
  }, []);

  // Trier par date
  chartData.sort((a, b) => a.metric_date.localeCompare(b.metric_date));

  // Obtenir la liste des villes uniques
  const cities = Array.from(new Set(windData.map(row => row.location)));

  if (chartData.length === 0) {
    return (
      <Card title="Vitesse du vent moyenne">
        <p>Aucune donnée de vent disponible</p>
      </Card>
    );
  }

  return (
    <Card title="Vitesse du vent moyenne par mois et par ville">
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="metric_date"
            tick={{ fontSize: 12 }}
          />
          <YAxis
            label={{ value: 'Vitesse du vent (km/h)', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip
            formatter={(value: number) => [`${value.toFixed(1)} km/h`, '']}
            labelFormatter={(label) => `Mois: ${label}`}
          />
          <Legend />
          {cities.map((city, index) => (
            <Line
              key={city}
              type="monotone"
              dataKey={city}
              stroke={`hsl(${index * 360 / cities.length + 120}, 70%, 50%)`}
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
};

export default WindSpeedChart;