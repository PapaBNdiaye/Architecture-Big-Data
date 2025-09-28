import React from 'react';
import { Table, Card } from 'antd';
import type { SortOrder } from 'antd/es/table/interface';
import type { Row } from '../types';

interface ResultsTableProps {
  data: Row[];
}

const ResultsTable: React.FC<ResultsTableProps> = ({ data }) => {
  const columns = [
    {
      title: 'Date',
      dataIndex: 'metric_date',
      key: 'metric_date',
      sorter: (a: Row, b: Row) => a.metric_date.localeCompare(b.metric_date),
      sortDirections: ['ascend', 'descend'] as SortOrder[],
    },
    {
      title: 'Ville',
      dataIndex: 'location',
      key: 'location',
      sorter: (a: Row, b: Row) => a.location.localeCompare(b.location),
      sortDirections: ['ascend', 'descend'] as SortOrder[],
    },
    {
      title: 'Métrique',
      dataIndex: 'metric_name',
      key: 'metric_name',
      render: (value: string) => {
        const labels: Record<string, string> = {
          'avg_temp_c': 'Température moyenne (°C)',
          'sum_precip_mm': 'Précipitations (mm)',
          'rainy_days': 'Jours pluvieux',
          'temp_amp_c': 'Amplitude thermique (°C)',
          'avg_humidity': 'Humidité relative (%)',
          'avg_windspeed': 'Vitesse du vent (km/h)',
        };
        return labels[value] || value;
      },
    },
    {
      title: 'Valeur',
      dataIndex: 'metric_value',
      key: 'metric_value',
      sorter: (a: Row, b: Row) => a.metric_value - b.metric_value,
      sortDirections: ['ascend', 'descend'] as SortOrder[],
      render: (value: number) => value.toFixed(2),
    },
    {
      title: 'Source',
      dataIndex: 'source',
      key: 'source',
    },
  ];

  return (
    <Card title="Résultats" style={{ marginBottom: 24 }}>
      <Table
        dataSource={data}
        columns={columns}
        rowKey={(record) => `${record.metric_date}-${record.location}-${record.metric_name}`}
        pagination={{
          pageSize: 5,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total, range) =>
            `${range[0]}-${range[1]} sur ${total} résultats`,
        }}
        scroll={{ x: 800 }}
      />
    </Card>
  );
};

export default ResultsTable;