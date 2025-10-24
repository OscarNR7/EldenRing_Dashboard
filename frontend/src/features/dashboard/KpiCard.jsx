import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import './KpiCard.css';

const KpiCard = ({ title, value }) => {
  return (
    <Card className="kpi-card">
      <CardHeader className="kpi-card-header">
        <CardTitle className="kpi-card-title">{title}</CardTitle>
      </CardHeader>
      <CardContent className="kpi-card-content">
        <div className="kpi-card-value">{value}</div>
      </CardContent>
    </Card>
  );
};

export default KpiCard;
