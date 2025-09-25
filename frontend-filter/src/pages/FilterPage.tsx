import React, { useState } from 'react';
import { Layout, Typography, message, Spin, Card, Row as AntRow, Col } from 'antd';
import { CloudOutlined, BarChartOutlined, LineChartOutlined, GlobalOutlined } from '@ant-design/icons';
import Filters from '../components/Filters';
import ResultsTable from '../components/ResultsTable';
import TempTrendChart from '../components/charts/TempTrendChart';
import PrecipByMonthChart from '../components/charts/PrecipByMonthChart';
import ThermalAmplitudeChart from '../components/charts/ThermalAmplitudeChart';
import CityImageMap from '../components/CityImageMap';
import type { Row as DataRow, RunPayload } from '../types';
import { apiService } from '../api';

const { Header, Content, Footer } = Layout;
const { Title, Text } = Typography;

const FilterPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<DataRow[]>([]);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);

  const handleRunQuery = async (payload: RunPayload) => {
    try {
      setLoading(true);
      const { task_id } = await apiService.runQuery(payload);
      setCurrentTaskId(task_id);
      message.info({
        content: '🔄 Calcul en cours... Traitement des données météo avec Spark',
        duration: 3,
        icon: <CloudOutlined style={{ color: '#1890ff' }} />
      });

      // Démarrer le monitoring du statut
      monitorTaskStatus(task_id);
    } catch (error: any) {
      message.error({
        content: `❌ Erreur lors du lancement: ${error.response?.data?.detail || error.message}`,
        duration: 5
      });
      setLoading(false);
    }
  };

  const monitorTaskStatus = (taskId: string) => {
    const checkStatus = async () => {
      try {
        const status = await apiService.getTaskStatus(taskId);
        if (status.state === 'SUCCESS') {
          // Récupérer les résultats
          const { data } = await apiService.fetchResults(taskId);
          setResults(data);
          setLoading(false);
          setCurrentTaskId(null);
          message.success({
            content: `✅ Analyse terminée ! ${data.length} mesures récupérées depuis HDFS`,
            duration: 5,
            icon: <BarChartOutlined style={{ color: '#52c41a' }} />
          });
        } else if (status.state === 'FAILURE') {
          message.error({
            content: '❌ Échec du traitement Spark',
            duration: 5
          });
          setLoading(false);
          setCurrentTaskId(null);
        } else {
          // Continuer à vérifier
          setTimeout(checkStatus, 2000);
        }
      } catch (error: any) {
        message.error({
          content: `❌ Erreur de récupération: ${error.response?.data?.detail || error.message}`,
          duration: 5
        });
        setLoading(false);
        setCurrentTaskId(null);
      }
    };

    checkStatus();
  };

  const handleCityClick = (city: string) => {
    message.info({
      content: `🌍 Détails météorologiques pour ${city} - Fonctionnalité en développement`,
      icon: <GlobalOutlined />
    });
  };

  return (
    <Layout style={{ minHeight: '100vh', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
      <Header style={{
        background: 'rgba(0, 21, 41, 0.9)',
        backdropFilter: 'blur(10px)',
        padding: '0 24px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <CloudOutlined style={{ fontSize: '32px', color: '#1890ff' }} />
          <div>
            <Title level={3} style={{ color: 'white', margin: '8px 0 0 0' }}>
              🏗️ Architecture Lambda - Panneau de Filtrage
            </Title>
            <Text style={{ color: 'rgba(255, 255, 255, 0.8)', fontSize: '14px' }}>
              Traitement batch météo avec Spark & HDFS
            </Text>
          </div>
        </div>
      </Header>

      <Content style={{
        padding: '24px',
        background: 'transparent',
        minHeight: 'calc(100vh - 134px)'
      }}>
        <AntRow gutter={[24, 24]}>
          <Col xs={24} lg={8}>
            <Card
              title={
                <span>
                  <LineChartOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                  Configuration des filtres
                </span>
              }
              style={{
                borderRadius: '12px',
                boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
                background: 'rgba(255, 255, 255, 0.95)',
                backdropFilter: 'blur(10px)'
              }}
            >
              <Filters onRunQuery={handleRunQuery} loading={loading} />
            </Card>
          </Col>

          <Col xs={24} lg={16}>
            {loading && (
              <Card
                style={{
                  textAlign: 'center',
                  borderRadius: '12px',
                  boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
                  background: 'rgba(255, 255, 255, 0.95)',
                  backdropFilter: 'blur(10px)'
                }}
              >
                <Spin size="large" />
                <Title level={4} style={{ marginTop: 16, color: '#1890ff' }}>
                  🔄 Traitement Spark en cours...
                </Title>
                <Text type="secondary">
                  Analyse des données météo avec l'architecture Lambda
                </Text>
                {currentTaskId && (
                  <div style={{ marginTop: 16 }}>
                    <Text code>Task ID: {currentTaskId}</Text>
                  </div>
                )}
              </Card>
            )}

            {results.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                <Card
                  title={
                    <span>
                      <BarChartOutlined style={{ marginRight: 8, color: '#52c41a' }} />
                      Résultats du traitement batch ({results.length} mesures)
                    </span>
                  }
                  style={{
                    borderRadius: '12px',
                    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
                    background: 'rgba(255, 255, 255, 0.95)',
                    backdropFilter: 'blur(10px)'
                  }}
                >
                  <ResultsTable data={results} />
                </Card>

                <Card
                  title={
                    <span>
                      📊 Analyses météorologiques - Données HDFS
                    </span>
                  }
                  style={{
                    borderRadius: '12px',
                    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
                    background: 'rgba(255, 255, 255, 0.95)',
                    backdropFilter: 'blur(10px)'
                  }}
                >
                  <AntRow gutter={[16, 16]}>
                    <Col xs={24} xl={12}>
                      <TempTrendChart data={results} />
                    </Col>
                    <Col xs={24} xl={12}>
                      <PrecipByMonthChart data={results} />
                    </Col>
                    <Col xs={24}>
                      <ThermalAmplitudeChart data={results} />
                    </Col>
                  </AntRow>
                </Card>

                <Card
                  title={
                    <span>
                      <GlobalOutlined style={{ marginRight: 8, color: '#722ed1' }} />
                      Carte interactive des villes
                    </span>
                  }
                  style={{
                    borderRadius: '12px',
                    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
                    background: 'rgba(255, 255, 255, 0.95)',
                    backdropFilter: 'blur(10px)'
                  }}
                >
                  <CityImageMap onCityClick={handleCityClick} weatherData={results} />
                </Card>
              </div>
            )}

            {results.length === 0 && !loading && (
              <Card
                style={{
                  textAlign: 'center',
                  borderRadius: '12px',
                  boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
                  background: 'rgba(255, 255, 255, 0.95)',
                  backdropFilter: 'blur(10px)',
                  minHeight: '300px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center'
                }}
              >
                <CloudOutlined style={{ fontSize: '64px', color: '#d9d9d9', marginBottom: 16 }} />
                <Title level={3} style={{ color: '#8c8c8c' }}>
                  Prêt pour l'analyse météo
                </Title>
                <Text style={{ color: '#8c8c8c', fontSize: '16px' }}>
                  Configurez vos filtres et lancez une requête pour voir les données traitées par Spark
                </Text>
              </Card>
            )}
          </Col>
        </AntRow>
      </Content>

      <Footer style={{
        textAlign: 'center',
        background: 'rgba(0, 21, 41, 0.9)',
        backdropFilter: 'blur(10px)',
        borderTop: '1px solid rgba(255, 255, 255, 0.1)',
        color: 'rgba(255, 255, 255, 0.8)'
      }}>
        <div style={{ marginBottom: 8 }}>
          <Text style={{ color: 'rgba(255, 255, 255, 0.8)' }}>
            🏗️ Architecture Lambda - Couche Batch | Spark + HDFS + Airflow
          </Text>
        </div>
        <a
          href="https://www.visualcrossing.com/"
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: '#1890ff' }}
        >
          📊 Weather Data Provided by Visual Crossing
        </a>
      </Footer>
    </Layout>
  );
};

export default FilterPage;