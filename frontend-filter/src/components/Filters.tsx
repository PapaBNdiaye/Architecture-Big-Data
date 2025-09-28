import React, { useState } from 'react';
import { Form, Input, DatePicker, Select, Button, Card, Space } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { RunPayload } from '../types';

const { RangePicker } = DatePicker;
const { Option } = Select;

interface FiltersProps {
  onRunQuery: (payload: RunPayload) => void;
  loading: boolean;
}

const Filters: React.FC<FiltersProps> = ({ onRunQuery, loading }) => {
  const [form] = Form.useForm();
  const [locations, setLocations] = useState<string[]>(['Paris,FR', 'Lyon,FR']);

  const availableMetrics = [
    { value: 'temp', label: 'Température' },
    { value: 'precip', label: 'Précipitations' },
    { value: 'windspeed', label: 'Vitesse du vent' },
    { value: 'humidity', label: 'Humidité' },
  ];

  const handleAddLocation = () => {
    setLocations([...locations, '']);
  };

  const handleLocationChange = (index: number, value: string) => {
    const newLocations = [...locations];
    newLocations[index] = value;
    setLocations(newLocations);
  };

  const handleRemoveLocation = (index: number) => {
    if (locations.length > 1) {
      setLocations(locations.filter((_, i) => i !== index));
    }
  };

  const handleSubmit = (values: any) => {
    const [startDate, endDate] = values.dateRange;
    const payload: RunPayload = {
      locations: locations.filter(loc => loc.trim() !== ''),
      startDate: startDate.format('YYYY-MM-DD'),
      endDate: endDate.format('YYYY-MM-DD'),
      granularity: values.granularity,
      metrics: values.metrics,
      agg: values.agg,
    };
    onRunQuery(payload);
  };

  return (
    <Card title="Filtres de requête" style={{ marginBottom: 24 }}>
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          granularity: 'days',
          metrics: ['temp', 'precip', 'humidity', 'windspeed'],
          agg: 'avg_by_month',
          dateRange: [dayjs('2023-01-01'), dayjs()],
        }}
      >
        <Form.Item label="Villes" required>
          <Space direction="vertical" style={{ width: '100%' }}>
            {locations.map((location, index) => (
              <Space key={index}>
                <Input
                  placeholder="ex: Paris,FR"
                  value={location}
                  onChange={(e) => handleLocationChange(index, e.target.value)}
                  style={{ width: 200 }}
                />
                {locations.length > 1 && (
                  <Button
                    type="text"
                    danger
                    onClick={() => handleRemoveLocation(index)}
                  >
                    Supprimer
                  </Button>
                )}
              </Space>
            ))}
            <Button
              type="dashed"
              onClick={handleAddLocation}
              icon={<PlusOutlined />}
            >
              Ajouter une ville
            </Button>
          </Space>
        </Form.Item>

        <Form.Item
          label="Période"
          name="dateRange"
          rules={[{ required: true, message: 'Veuillez sélectionner une période' }]}
        >
          <RangePicker
            format="YYYY-MM-DD"
            style={{ width: '100%' }}
          />
        </Form.Item>

        <Form.Item
          label="Granularité"
          name="granularity"
          rules={[{ required: true }]}
        >
          <Select>
            <Option value="days">Jours</Option>
            <Option value="hours">Heures</Option>
          </Select>
        </Form.Item>

        <Form.Item
          label="Métriques"
          name="metrics"
          rules={[{ required: true, message: 'Sélectionnez au moins une métrique' }]}
        >
          <Select mode="multiple" placeholder="Sélectionnez les métriques">
            {availableMetrics.map(metric => (
              <Option key={metric.value} value={metric.value}>
                {metric.label}
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          label="Agrégation"
          name="agg"
          rules={[{ required: true }]}
        >
          <Select>
            <Option value="avg_by_month">Moyenne par mois</Option>
            <Option value="sum_by_month">Somme par mois</Option>
            <Option value="compare_locations">Comparaison des villes</Option>
          </Select>
        </Form.Item>

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            disabled={locations.filter(loc => loc.trim() !== '').length === 0}
            block
          >
            Lancer la requête
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default Filters;