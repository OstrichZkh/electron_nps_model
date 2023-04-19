import React, { useState } from "react";
import Title from "../../components/Title";
import { DatePicker, Button } from "antd";
import styled from "styled-components";
import dayjs from "dayjs";
import { useSelector, useDispatch } from "react-redux";
import {
  updateStatus,
  getProjectInfoAsync,
  getStatus,
  updateStatusAsync,
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
  let { startDate, endDate } = curProjectInfo.periods;
  let dispatch = useDispatch();
  const [periods, setPeriods]: [string[], Function] = useState([
    startDate ? startDate : "2016/01",
    endDate ? endDate : "2017/01",
  ]);

  const onDataChange = (e) => {
    let startD =
      e[0].$y + "/" + (Number(e[0].$M) < 9 ? "0" + (e[0].$M + 1) : e[0].$M + 1);
    let endD =
      e[1].$y + "/" + (Number(e[1].$M) < 9 ? "0" + (e[1].$M + 1) : e[1].$M + 1);
    setPeriods([startD, endD]);
  };

  const submitDate = () => {
    let payload = [
      { target: ["periods", "startDate"], value: periods[0] },
      { target: ["periods", "endDate"], value: periods[1] },
    ];
    dispatch(updateStatusAsync(payload));
  };

  return (
    <SimRangeBox>
      <Title title="模拟期选择" />
      <RangePicker
        defaultValue={[
          dayjs(periods[0], "YYYY/MM"),
          dayjs(periods[1], "YYYY/MM"),
        ]}
        style={{ width: "30rem", marginBottom: "1rem" }}
        size="large"
        picker="month"
        onChange={onDataChange}
      />
      <Button onClick={submitDate} type="primary" style={{ width: "10rem" }}>
        确认
      </Button>
    </SimRangeBox>
  );
}

export default SimRangeView;
