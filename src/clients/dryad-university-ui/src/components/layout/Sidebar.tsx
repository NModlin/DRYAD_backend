import React from 'react'

export const Sidebar: React.FC = () => {
    return (
        <aside className="w-64 bg-gray-800 text-white min-h-screen p-4">
            <nav>
                <ul>
                    <li><a href="/" className="block py-2">Dashboard</a></li>
                    <li><a href="/universities" className="block py-2">Universities</a></li>
                </ul>
            </nav>
        </aside>
    )
}
