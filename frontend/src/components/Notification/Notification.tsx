/**
 * 通知组件
 */

import React from 'react';
import { CheckCircle, XCircle, Info, X } from 'lucide-react';
import { useAppStore } from '../../stores';
import './Notification.css';

const Notification: React.FC = () => {
    const { notification, clearNotification } = useAppStore();

    if (!notification) return null;

    const icons = {
        success: <CheckCircle size={20} />,
        error: <XCircle size={20} />,
        info: <Info size={20} />,
    };

    return (
        <div className={`notification notification--${notification.type}`}>
            <div className="notification__icon">{icons[notification.type]}</div>
            <span className="notification__message">{notification.message}</span>
            <button className="notification__close" onClick={clearNotification}>
                <X size={16} />
            </button>
        </div>
    );
};

export default Notification;
