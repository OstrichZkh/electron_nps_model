import React from "react";
import Title from "../../components/Title";
import styled from "styled-components";
import FileImporter from "../../components/FileImporter";
const RainfallViewBox = styled.div`
  padding: 1rem;
  display: flex;
  flex-direction: column;
`;

function RainfallView() {
  return (
    <RainfallViewBox>
      <Title title="降雨数据" />
      <FileImporter type="rainfall" svg="" />
    </RainfallViewBox>
  );
}

export default RainfallView;
