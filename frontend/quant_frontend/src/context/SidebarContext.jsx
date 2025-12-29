import React, { createContext, useContext, useState } from 'react';

const SidebarContext = createContext();

export const SidebarProvider = ({ children }) => {
    const [expanded, setExpanded] = useState(true);

    const toggleSidebar = () => {
        setExpanded((prev) => !prev);
    };

    return (
        <SidebarContext.Provider value={{ expanded, setExpanded, toggleSidebar }}>
            {children}
        </SidebarContext.Provider>
    );
};

export const useSidebar = () => useContext(SidebarContext);
