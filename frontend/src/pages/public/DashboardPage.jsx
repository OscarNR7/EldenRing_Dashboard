import React, { useEffect } from 'react';
import HeroBanner from '../../features/dashboard/HeroBanner';
import KpiCard from '../../features/dashboard/KpiCard';
import AnalyticsCharts from '../../features/dashboard/AnalyticsCharts';
import BossCarousels from '../../features/dashboard/BossCarousels';
import LoadingSpinner from '../../components/LoadingSpinner';
import useFetchData from '../../hooks/useFetchData';
import { getWeapons, getWeaponStatistics } from '../../lib/weaponService';
import { getBosses } from '../../lib/bossService';
import { getArmors } from '../../lib/armorService';
import { getClasses } from '../../lib/classService';

const DashboardPage = () => {
  const { data, loading, error, execute } = useFetchData();

  useEffect(() => {
    const fetchDashboardData = async () => {
      const [weaponsRes, bossesRes, armorsRes, classesRes, weaponStatsRes] = await Promise.all([
        getWeapons({ limit: 1 }), // Solo necesitamos 1 para obtener el total
        getBosses({ limit: 500 }), // Obtener todos los jefes para carruseles y gráficos (nuevo límite)
        getArmors({ limit: 1 }),
        getClasses({ limit: 1 }),
        getWeaponStatistics(),
      ]);
      
      return {
        totalWeapons: weaponsRes.total,
        totalBosses: bossesRes.total,
        totalArmors: armorsRes.total,
        totalClasses: classesRes.total,
        bosses: bossesRes.items, // Lista completa de jefes
        weaponStats: weaponStatsRes, // Estadísticas de armas para el gráfico
      };
    };

    execute(fetchDashboardData);
  }, [execute]);

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <div className="container">Error: {error.message}</div>;
  }

  const kpis = data ? [
    { title: "Total de Armas", value: data.totalWeapons },
    { title: "Total de Jefes", value: data.totalBosses },
    { title: "Total de Armaduras", value: data.totalArmors },
    { title: "Total de Clases", value: data.totalClasses },
  ] : [];

  return (
    <div className="dashboard-page">
      <HeroBanner />
      <div className="container">
        <h2 style={{ textAlign: 'center', marginBottom: '2rem', color: 'var(--color-accent-gold)' }}>Estadísticas Rápidas</h2>
        <div className="kpi-grid">
          {kpis.map((kpi, index) => (
            <KpiCard key={index} title={kpi.title} value={kpi.value} />
          ))}
        </div>

        {data && data.bosses && data.weaponStats && (
          <AnalyticsCharts bosses={data.bosses} weaponStats={data.weaponStats} />
        )}

        {data && data.bosses && (
          <BossCarousels bosses={data.bosses} />
        )}
      </div>
    </div>
  );
};

export default DashboardPage;