import { createContext, useContext, useState } from 'react';

const AppContext = createContext();

export const useAppContext = () => useContext(AppContext);

export const AppProvider = ({ children }) => {
  // --- People Merge State ---
  const initialPeopleState = {
    step: 0,
    uploadedFiles: [null, null, null],
    verifiedFiles: [],
    fileMappings: {},
    globalSuggestedMappings: {},
    keyColumns: [],
    availableHeaders: [],
    result: null,
    previewStates: {},
  };
  const [peopleState, setPeopleState] = useState(initialPeopleState);
  const resetPeopleState = () => setPeopleState(initialPeopleState);

  // --- Info Append State ---
  const initialInfoState = {
    step: 0,
    masterFile: null,
    auxFiles: [null, null],
    keyColumns: [],
    mappings: [],
    result: null,
  };
  const [infoState, setInfoState] = useState(initialInfoState);
  const resetInfoState = () => setInfoState(initialInfoState);

  // --- Goods Merge State ---
  const initialGoodsState = {
    step: 0,
    inputFile: null,
    catalogFile: null,
    matchColumn: '',
    result: null,
    activeTab: 'Pending',
  };
  const [goodsState, setGoodsState] = useState(initialGoodsState);
  const resetGoodsState = () => setGoodsState(initialGoodsState);

  // --- Dynamic Pivot State ---
  const initialPivotState = {
    step: 0,
    uploadedFile: null,
    sourceColumns: [],
    ignoreCase: true,
    multiValueSeparator: '',
    analysisResult: null,
    columnConfigs: [],
    markSymbol: 'x',
    placement: 'Replace',
    previewResult: null,
  };
  const [pivotState, setPivotState] = useState(initialPivotState);
  const resetPivotState = () => setPivotState(initialPivotState);

  // --- Unpivot (Ngang → Dọc) State ---
  const initialUnpivotState = {
    step: 0,
    uploadedFile: null,
    allHeaders: [],       // Tất cả cột của file
    unpivotColumns: [],   // Các cột được chọn để unpivot
    attributeColumnName: 'Danh mục',
    valueColumnName: 'Giá trị',
    includeValueColumn: false,
    skipEmptyValues: true,
    previewResult: null,
  };
  const [unpivotState, setUnpivotState] = useState(initialUnpivotState);
  const resetUnpivotState = () => setUnpivotState(initialUnpivotState);

  const [headerCenterContent, setHeaderCenterContent] = useState(null);

  return (
    <AppContext.Provider
      value={{
        peopleState, setPeopleState, resetPeopleState,
        infoState, setInfoState, resetInfoState,
        goodsState, setGoodsState, resetGoodsState,
        pivotState, setPivotState, resetPivotState,
        unpivotState, setUnpivotState, resetUnpivotState,
        headerCenterContent, setHeaderCenterContent,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};
