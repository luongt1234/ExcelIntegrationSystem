import api from './api';

// ── Auth ──────────────────────────────────────────────
export const login = (username, password) =>
  api.post('/api/auth/login', { username, password });

// ── Upload / Excel ────────────────────────────────────
export const uploadFile = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/api/excel/upload', formData, {
    headers: {
      'Content-Type': undefined
    }
  });
};

export const getFileStructure = (fileId, sheetName = null) => {
  let url = `/api/excel/${fileId}/structure`;
  if (sheetName) url += `?sheetName=${encodeURIComponent(sheetName)}`;
  return api.get(url);
};

export const getFileData = (fileId, sheetName = null) => {
  let url = `/api/excel/${fileId}/data`;
  if (sheetName) url += `?sheetName=${encodeURIComponent(sheetName)}`;
  return api.get(url);
};

// ── People Merge (Feature 1) ──────────────────────────
export const mergePeople = (fileIds, config) =>
  api.post('/api/peopleMerge/merge', { fileIds, ...config });

export const exportPeopleResult = (rows) =>
  api.post('/api/peopleMerge/export', { rows }, { responseType: 'blob' });

// ── Info Append / Left Join (Feature 2) ──────────────
export const leftJoin = (masterFileId, auxFileIds, mappings, keyColumns, selectedSheetByFile = null) =>
  api.post('/api/infoAppend/join', { masterFileId, auxFileIds, mappings, keyColumns, selectedSheetByFile });

export const exportInfoAppendResult = (rows) =>
  api.post('/api/infoAppend/export', { rows }, { responseType: 'blob' });

// ── Goods Merge (Feature 3) ───────────────────────────
export const matchGoods = (inputFileId, catalogFileId, matchColumn) =>
  api.post('/api/goodsMerge/match', { inputFileId, catalogFileId, matchColumn });

export const exportGoodsResult = (result) =>
  api.post('/api/goodsMerge/export', result, { responseType: 'blob' });

// ── Utility: Trigger download từ blob response ─────────
export const downloadBlob = (response, fileName) => {
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', fileName);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};
