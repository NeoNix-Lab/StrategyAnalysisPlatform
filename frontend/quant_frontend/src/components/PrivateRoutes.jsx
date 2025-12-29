import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const PrivateRoutes = () => {
    const { user, isLoading } = useAuth();

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-900 text-gray-100">
                Loading...
            </div>
        );
    }

    return user ? <Outlet /> : <Navigate to="/login" />;
};

export default PrivateRoutes;
