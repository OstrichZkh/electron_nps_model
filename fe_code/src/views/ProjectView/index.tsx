import React, { useCallback, useEffect, useState } from "react";
import SiderBar from "./components/siderBar";
import styled from "styled-components";
import { ProjectInfo } from "../../interface/index.ts";
import { ReactSVG } from "react-svg";
import file from "../../assets/svgs/file.svg";
import { Button, Modal } from "antd";
import {
  updateStatus,
  getProjectInfoAsync,
  getStatus,
} from "../../store/features/dataManagementSlice.ts";
import { useSelector, useDispatch } from "react-redux";
import { CheckOutlined, CloseOutlined } from "@ant-design/icons";

const ProjectViewBox = styled.div`
  display: flex;
  height: 100vh;
  /* width: 80vw; */
  .page-title {
    margin: 1rem;
    font-size: 1.5rem;
    font-weight: 800;
    font-family: "consolas", Times, serif;
  }
  .page-dir {
    padding: 0.15rem 0;
    margin: 0 1.5rem;
    height: 2rem;
    background: rgb(248, 249, 250);
    border: 0.05rem solid rgb(222, 226, 230);
    line-height: 2rem;
    white-space: nowrap;
    font-family: "consolas";
    border-radius: 0.4rem;
    display: flex;
    width: 100%;
    svg {
      vertical-align: middle;
      padding: 0 0.6rem;
      width: 1.2rem;
      height: 1.2rem;
    }
    &:hover {
      cursor: pointer;
      background-color: rgb(226, 230, 234);
    }
  }
  .page-info {
    width: 80vw;
    margin: 0 1.5rem;
    .page-info-title {
      text-align: center;
      margin: 0 auto;
      margin-top: 1rem;
      margin-bottom: 0.5rem;
      font-weight: bold;
    }
    .project-info {
      margin: 0px 30px;
      display: flex;
      flex-wrap: wrap;
      font-size: 1rem;
    }
    .project-info-item {
      border-top: 1px solid rgb(222, 226, 230);
      border-bottom: 1px solid rgb(222, 226, 230);
      margin-top: -1px;
      width: 25%;
      padding: 5px 0;
    }
    .sub-title {
      font-weight: 600;
    }
  }
  .page-data {
    margin: 0 30px;
    margin-top: 50px;
    font-weight: bold;
    font-family: "Times New Roman", Times, serif;
    .page-data-title {
      margin-bottom: 0.5rem;
    }
    .page-data-item {
      border-top: 1px solid rgb(222, 226, 230);
      border-bottom: 1px solid rgb(222, 226, 230);
      margin-top: -1px;
      width: 100%;
      padding: 5px 0;
      display: flex;
      svg {
        width: 20px;
        padding-right: 10px;
      }
      .page-data-item-title {
        font-weight: 100;
        color: rgb(58, 138, 207);
      }
      .page-data-item-title:hover {
        text-decoration: underline;
        cursor: pointer;
      }
    }
  }
`;

function ProjectView() {
  // 获取公共状态
  let { allProjectInfos, curProjectInfo } = useSelector(
    (state) => state.dataManagementReducer
  );
  let dispatch = useDispatch();
  // 首次渲染查询项目信息
  useEffect(() => {
    if (allProjectInfos.length === 0) {
      dispatch(getProjectInfoAsync());
    }
  }, []);

  // 询问是否删除项目
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [confirmLoading, setConfirmLoading] = useState(false);
  const showModal = () => {
    setIsModalOpen(true);
  };
  const handleOk = async () => {
    setConfirmLoading(true);
    let res = await window.electronAPI.deleteProject(
      curProjectInfo.projectName
    );
    if (res.status === 200) {
      setIsModalOpen(false);
      setConfirmLoading(false);
      dispatch(getProjectInfoAsync());
    }
  };
  const handleCancel = () => {
    setIsModalOpen(false);
  };
  return (
    <ProjectViewBox>
      <SiderBar />
      {curProjectInfo && (
        <div className="page-container">
          {/* 标题 */}
          <div className="page-title">
            目前项目:{curProjectInfo.projectName}
          </div>
          {/* 文件夹位置 */}
          <div className="page-dir">
            <ReactSVG src={file} />
            {curProjectInfo.projectPath}
          </div>
          {/* 项目信息 */}
          <div className="page-info">
            <div className="page-info-title">数据信息</div>
            <div className="project-info">
              <div className="project-info-item sub-title">流域面积</div>
              <div className="project-info-item">110.5 ha</div>
              <div className="project-info-item sub-title">模拟期</div>
              <div className="project-info-item">2010-2021</div>
              <div className="project-info-item sub-title">栅格数量</div>
              <div className="project-info-item">9635</div>
              <div className="project-info-item sub-title">最近保存</div>
              <div className="project-info-item">2022-8-23 9:09</div>
            </div>
          </div>
          {/* 数据信息 */}
          <div className="page-data">
            <div className="page-data-title">数据信息</div>
            {Object.keys(curProjectInfo).map((key: string) => {
              if (
                ["rainfall", "DEM", "landUse", "soilType", "D8"].indexOf(
                  key
                ) !== -1
              ) {
                let title: string = "";
                let status: boolean = curProjectInfo[key].status;
                switch (key) {
                  case "rainfall":
                    title = "降雨数据";
                    break;
                  case "DEM":
                    title = "DEM";
                    break;
                  case "landUse":
                    title = "土地利用数据";
                    break;
                  case "soilType":
                    title = "土壤类型数据";
                    break;
                  case "D8":
                    title = "流向数据";
                    break;
                }
                return (
                  <div className="page-data-item" key={key}>
                    {status === true ? <CheckOutlined /> : <CloseOutlined />}
                    <div className="page-data-item-title">{title}</div>
                  </div>
                );
              } else if (key === "rusle") {
                // const { S_factor, L_factor, C_factor } = curProjectInfo[key];
                return Object.keys(curProjectInfo[key]).map((factor) => {
                  let status: boolean = curProjectInfo[key][factor];
                  let title: string = factor[0] + "因子";
                  return (
                    <div className="page-data-item" key={title}>
                      {status === true ? <CheckOutlined /> : <CloseOutlined />}
                      <div className="page-data-item-title">{title}</div>
                    </div>
                  );
                });
              }
            })}
          </div>
          <Button
            onClick={showModal}
            style={{ margin: "1.5rem" }}
            type="primary"
            danger
          >
            删除项目
          </Button>
          <Modal
            title="是否删除项目，此操作不可逆"
            cancelText="取消"
            confirmLoading={confirmLoading}
            okText="确定删除"
            okType="primary"
            open={isModalOpen}
            onOk={handleOk}
            onCancel={handleCancel}
          ></Modal>
        </div>
      )}
    </ProjectViewBox>
  );
}

export default ProjectView;
