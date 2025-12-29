import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { TradeReplayer } from '../components/TradeReplayer';

// Simple wrapper page
const TradeReplayPage = () => {
    const { tradeId } = useParams();
    const navigate = useNavigate();

    return (
        <div style={{ width: '100%', height: '100vh', background: '#0f172a' }}>
            {/* We render the Replayer Modal directly. When closed, go back. */}
            <TradeReplayer
                tradeId={tradeId}
                onClose={() => navigate(-1)}
            />
        </div>
    );
};

export default TradeReplayPage;
