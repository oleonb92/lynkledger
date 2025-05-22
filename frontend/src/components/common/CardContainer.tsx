import React from 'react';
import { Card, CardContent, CardProps } from '@mui/material';

interface CardContainerProps extends CardProps {
  children: React.ReactNode;
}

const CardContainer: React.FC<CardContainerProps> = ({ children, ...props }) => (
  <Card {...props} sx={{ borderRadius: 6, ...props.sx }}>
    <CardContent>
      {children}
    </CardContent>
  </Card>
);

export default CardContainer; 