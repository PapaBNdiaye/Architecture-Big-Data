import React from 'react';
import { Card } from 'antd';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { Row } from '../../types';

interface ThermalAmplitudeChartProps {
  data: Row[];
}

const ThermalAmplitudeChart: React.FC<ThermalAmplitudeChartProps> = ({ data }) => {
  // Filtrer les données d'amplitude thermique
  const amplitudeData = data.filter(row => row.metric_name === 'temp_amp_c');

  // Transformer les données pour Recharts
  const chartData = amplitudeData.reduce((acc: any[], row) => {
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
  const cities = Array.from(new Set(amplitudeData.map(row => row.location)));

  if (chartData.length === 0) {
    return (
      <Card title="Amplitude thermique">
        <p>Aucune donnée d'amplitude thermique disponible</p>
      </Card>
    );
  }

  return (
    <Card title="Amplitude thermique (Max-Min) par mois et par ville">
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="metric_date"
            tick={{ fontSize: 12 }}
          />
          <YAxis
            label={{ value: 'Amplitude (°C)', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip
            formatter={(value: number) => [`${value.toFixed(1)}°C`, '']}
            labelFormatter={(label) => `Mois: ${label}`}
          />
          <Legend />
          {cities.map((city, index) => (
            <Bar
              key={city}
              dataKey={city}
              fill={`hsl(${index * 360 / cities.length + 60}, 70%, 50%)`}
              radius={[2, 2, 0, 0]}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
};

export default ThermalAmplitudeChart;