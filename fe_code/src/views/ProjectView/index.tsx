import React, { useState } from "react";
import SiderBar from "./components/siderBar";
import styled from "styled-components";
import { ProjectInfo } from "../../interface/index.ts";
import { ReactSVG } from "react-svg";
import file from "../../assets/svgs/file.svg";

const ProjectViewBox = styled.div`
  display: flex;
  width: 90vw;
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
`;

function ProjectView() {
  let [curProjectInfo, setCurProjectInfo]: [ProjectInfo | any, Function] =
    useState(null);

  return (
    <ProjectViewBox>
      <SiderBar setCurProjectInfo={setCurProjectInfo} />
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
        </div>
      )}
    </ProjectViewBox>
  );
}

export default ProjectView;
