import { Navigate, Outlet } from 'react-router-dom';
import { useAppSelector } from '../../store';

const PrivateRoute = () => {
  const { isAuthenticated } = useAppSelector((state) => state.auth);

  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
};

export default PrivateRoute; 