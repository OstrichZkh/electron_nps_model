import React from "react";
import Title from "../../components/Title";
import { DatePicker, Button } from "antd";
import styled from "styled-components";
import dayjs from "dayjs";
import { useSelector, useDispatch } from "react-redux";
import {
  updateStatus,
  getProjectInfoAsync,
  getStatus,
} from "../../store/features/dataManagementSlice.ts";

const { RangePicker } = DatePicker;

const SimRangeBox = styled.div`
  padding: 1rem;
  display: flex;
  flex-direction: column;
  .RangePicker {
    width: 10px;
  }
`;

function SimRangeView() {
  let { curProjectInfo } = useSelector((state) => state.dataManagementReducer);
  console.log(curProjectInfo);
  const onDataChange = (e) => {
    console.log(e);
  };
  return (
    <SimRangeBox>
      <Title title="模拟期选择" />
      <RangePicker
        defaultValue={[
          dayjs("2015/01", "YYYY/MM"),
          dayjs("2016/01", "YYYY/MM"),
        ]}
        style={{ width: "30rem", marginBottom: "1rem" }}
        size="large"
        picker="month"
        onChange={onDataChange}
      />
      <Button type="primary" style={{ width: "10rem" }}>
        确认
      </Button>
    </SimRangeBox>
  );
}

export default SimRangeView;
