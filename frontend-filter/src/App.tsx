import { ConfigProvider } from 'antd';
import FilterPage from './pages/FilterPage';
import './App.css';

function App() {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#1890ff',
        },
      }}
    >
      <FilterPage />
    </ConfigProvider>
  );
}

export default App;
