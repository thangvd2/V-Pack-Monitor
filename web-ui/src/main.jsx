/**
 * V-Pack Monitor - CamDongHang v1.10.0
 * Copyright (c) 2024-2026 VDT - Vu Duc Thang (thangvd2)
 * All rights reserved. Unauthorized copying or distribution is prohibited.
 */

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
