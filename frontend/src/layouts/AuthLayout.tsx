import React from 'react';
import { Outlet, Navigate } from 'react-router-dom';
import { Box } from '@mui/material';
import { useAppSelector } from '../store';

const AuthLayout = () => {
  const { isAuthenticated } = useAppSelector((state) => state.auth);

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'linear-gradient(120deg, #181c22 0%, #232a34 100%)' }}>
      <Box sx={{ width: '100%', maxWidth: 420, mx: 'auto' }}>
        <Outlet />
      </Box>
    </Box>
  );
};

export default AuthLayout; 