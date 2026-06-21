import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
} from '@mui/material';
import {
  RadialBarChart,
  RadialBar,
  ResponsiveContainer,
} from 'recharts';

interface GaugeProps {
  title: string;
  value: number;
  maxValue: number;
  unit?: string;
}

function Gauge({ title, value, maxValue, unit = '' }: GaugeProps) {
  const percentage = (value / maxValue) * 100;
  const color = percentage > 80 ? '#ef4444' : percentage > 50 ? '#f59e0b' : '#22c55e';

  const data = [{ name: title, value: percentage, fill: color }];

  return (
    <Card>
      <CardContent>
        <Typography variant="subtitle2" align="center" gutterBottom>
          {title}
        </Typography>
        <ResponsiveContainer width="100%" height={150}>
          <RadialBarChart
            cx="50%"
            cy="50%"
            innerRadius="60%"
            outerRadius="80%"
            data={data}
            startAngle={180}
            endAngle={0}
          >
            <RadialBar dataKey="value" cornerRadius={10} fill={color} />
          </RadialBarChart>
        </ResponsiveContainer>
        <Typography variant="h6" align="center">
          {value.toFixed(2)}{unit}
        </Typography>
      </CardContent>
    </Card>
  );
}

export default function RiskGaugeGrid() {
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        风险指标
      </Typography>
      <Grid container spacing={2}>
        <Grid item xs={12} sm={6} md={3}>
          <Gauge title="杠杆率" value={1.5} maxValue={5} unit="x" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Gauge title="单笔最大亏损" value={2.5} maxValue={10} unit="%" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Gauge title="VaR (95%)" value={3.2} maxValue={10} unit="%" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Gauge title="最大回撤" value={8.5} maxValue={20} unit="%" />
        </Grid>
      </Grid>
    </Box>
  );
}
