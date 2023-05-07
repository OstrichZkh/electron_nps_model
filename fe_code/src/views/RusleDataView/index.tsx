import React, { useState, useEffect } from "react";
import Title from "../../components/Title";
import styled from "styled-components";
import FileImporter from "../../components/FileImporter";
import { useSelector, useDispatch } from "react-redux";
const RusleViewBox = styled.div`
  padding: 1rem;
  display: flex;
  flex-direction: column;
`;
function RusledataView() {
  return (
    <RusleViewBox>
      <Title title="C因子" />
      <FileImporter type="C_factor" svg="" />
      <div style={{ height: "2rem" }}></div>
      <Title title="L因子" />
      <FileImporter type="L_factor" svg="" />
      <div style={{ height: "2rem" }}></div>
      <Title title="S因子" />
      <FileImporter type="S_factor" svg="" />
      <div style={{ height: "2rem" }}></div>
      <Title title="坡度" />
      <FileImporter type="slope" svg="" />
      <div style={{ height: "2rem" }}></div>
      <Title title="D8" />
      <FileImporter type="D8" svg="" />
      <div style={{ height: "2rem" }}></div>
    </RusleViewBox>
  );
}

export default RusledataView;
