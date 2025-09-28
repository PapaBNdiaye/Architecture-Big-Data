import React, { useState, useEffect } from 'react';
import { Card, Select, Space, Button } from 'antd';
import { FilterOutlined, ClearOutlined } from '@ant-design/icons';
import type { Row } from '../types';

const { Option } = Select;

interface ChartFiltersProps {
  data: Row[];
  onFiltersChange: (filters: ChartFiltersState) => void;
}

export interface ChartFiltersState {
  selectedCities: string[];
  selectedMetrics: string[];
}

const ChartFilters: React.FC<ChartFiltersProps> = ({ data, onFiltersChange }) => {
  // Extraire les villes et métriques uniques disponibles
  const availableCities = Array.from(new Set(data.map(row => row.location))).sort();
  const availableMetrics = Array.from(new Set(data.map(row => row.metric_name))).sort();

  // État des filtres
  const [selectedCities, setSelectedCities] = useState<string[]>(availableCities);
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>(availableMetrics);

  // Mettre à jour les filtres quand les données changent
  useEffect(() => {
    const newCities = Array.from(new Set(data.map(row => row.location))).sort();
    const newMetrics = Array.from(new Set(data.map(row => row.metric_name))).sort();

    setSelectedCities(newCities);
    setSelectedMetrics(newMetrics);

    onFiltersChange({
      selectedCities: newCities,
      selectedMetrics: newMetrics,
    });
  }, [data, onFiltersChange]);

  // Gestionnaire de changement des villes
  const handleCitiesChange = (values: string[]) => {
    setSelectedCities(values);
    onFiltersChange({
      selectedCities: values,
      selectedMetrics,
    });
  };

  // Gestionnaire de changement des métriques
  const handleMetricsChange = (values: string[]) => {
    setSelectedMetrics(values);
    onFiltersChange({
      selectedCities,
      selectedMetrics: values,
    });
  };

  // Réinitialiser les filtres
  const handleResetFilters = () => {
    setSelectedCities(availableCities);
    setSelectedMetrics(availableMetrics);
    onFiltersChange({
      selectedCities: availableCities,
      selectedMetrics: availableMetrics,
    });
  };

  // Labels lisibles pour les métriques
  const getMetricLabel = (metric: string): string => {
    const labels: Record<string, string> = {
      'avg_temp_c': 'Température',
      'sum_precip_mm': 'Précipitations',
      'avg_humidity': 'Humidité',
      'avg_windspeed': 'Vitesse du vent',
    };
    return labels[metric] || metric;
  };

  return (
    <Card
      title={
        <span>
          <FilterOutlined style={{ marginRight: 8, color: '#1890ff' }} />
          Filtres des graphiques
        </span>
      }
      size="small"
      style={{ marginBottom: 16 }}
    >
      <Space wrap>
        <div>
          <label style={{ display: 'block', marginBottom: 4, fontWeight: 'bold' }}>
            Villes à afficher :
          </label>
          <Select
            mode="multiple"
            placeholder="Sélectionnez les villes"
            value={selectedCities}
            onChange={handleCitiesChange}
            style={{ minWidth: 200 }}
            maxTagCount={3}
          >
            {availableCities.map(city => (
              <Option key={city} value={city}>
                {city}
              </Option>
            ))}
          </Select>
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: 4, fontWeight: 'bold' }}>
            Métriques à afficher :
          </label>
          <Select
            mode="multiple"
            placeholder="Sélectionnez les métriques"
            value={selectedMetrics}
            onChange={handleMetricsChange}
            style={{ minWidth: 200 }}
            maxTagCount={3}
          >
            {availableMetrics.map(metric => (
              <Option key={metric} value={metric}>
                {getMetricLabel(metric)}
              </Option>
            ))}
          </Select>
        </div>

        <Button
          icon={<ClearOutlined />}
          onClick={handleResetFilters}
          style={{ marginTop: 22 }}
        >
          Réinitialiser
        </Button>
      </Space>
    </Card>
  );
};

export default ChartFilters;