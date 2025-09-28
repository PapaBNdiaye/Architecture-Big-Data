import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { Icon } from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { Row } from '../types';

// Fix pour les icônes Leaflet par défaut
delete (Icon.Default.prototype as any)._getIconUrl;
Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Positions de test simplifiées
const cityCoordinates: Record<string, { lat: number; lng: number; name: string }> = {
  'Paris,FR': { lat: 48.8566, lng: 2.3522, name: 'Paris' },
  'Lyon,FR': { lat: 45.7640, lng: 4.8357, name: 'Lyon' },
};

interface CityImageMapProps {
  onCityClick: (city: string) => void;
  weatherData?: Row[];
}

const CityImageMap: React.FC<CityImageMapProps> = ({ onCityClick, weatherData = [] }) => {
  console.log('CityImageMap rendered with data:', weatherData);

  return (
    <div style={{ height: '500px', width: '100%', border: '2px solid red', position: 'relative' }}>
      <div style={{
        position: 'absolute',
        top: '10px',
        left: '10px',
        background: 'yellow',
        padding: '5px',
        zIndex: 1000,
        fontSize: '12px'
      }}>
        Debug: {weatherData.length} données météo
      </div>

      <MapContainer
        center={[46.603354, 1.888334]} // Centre de la France
        zoom={6}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {Object.entries(cityCoordinates).map(([cityKey, coords]) => {
          const hasWeatherData = weatherData.some(row => row.location === cityKey);

          return (
            <Marker
              key={cityKey}
              position={[coords.lat, coords.lng]}
              eventHandlers={{
                click: () => {
                  console.log('Marker clicked:', cityKey);
                  onCityClick(cityKey);
                },
              }}
            >
              <Popup>
                <div>
                  <h3>� {coords.name}</h3>
                  <p>Clé: {cityKey}</p>
                  {hasWeatherData ? (
                    <p style={{ color: 'green' }}>✅ Données météo disponibles</p>
                  ) : (
                    <p style={{ color: 'red' }}>❌ Pas de données météo</p>
                  )}
                  <button onClick={() => onCityClick(cityKey)}>
                    Voir les détails
                  </button>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
};

export default CityImageMap;