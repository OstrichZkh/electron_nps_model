import React from "react";
import Title from "../../components/Title";
import styled from "styled-components";
import { useSelector, useDispatch } from "react-redux";

type IProps = {};
const FertViewBox = styled.div`
  padding: 1rem;
  display: flex;
  flex-direction: column;
`;

const FertView = (props: IProps) => {
  let { curProjectInfo } = useSelector(
    (state: any) => state.dataManagementReducer
  );

  return (
    <FertViewBox>
      <Title title="农业措施设置" />
    </FertViewBox>
  );
};

export default FertView;
